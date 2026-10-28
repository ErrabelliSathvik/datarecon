import sqlite3

import pandas as pd
import pytest

from datarecon.publishing import publish_orders


def sample_orders():
    return pd.DataFrame([
        {
            "order_id": "1001",
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": 500.0,
            "status": "completed",
        },
        {
            "order_id": "1002",
            "customer_id": "C002",
            "order_date": "2026-10-25",
            "amount": 1200.0,
            "status": "pending",
        },
    ])


def test_rerunning_batch_does_not_duplicate_orders(tmp_path):
    database = str(tmp_path / "target.db")
    orders = sample_orders()

    first_run = publish_orders(
        orders, database, "batch_001", "source.csv"
    )
    second_run = publish_orders(
        orders, database, "batch_001", "source.csv"
    )

    assert first_run["target_count_after"] == 2

    with sqlite3.connect(database) as connection:
        order_count = connection.execute(
            "SELECT COUNT(*) FROM target_orders"
        ).fetchone()[0]

    assert order_count == 2
    assert second_run["new_rows"] == 0
    assert second_run["already_published"] is True


def test_new_batch_updates_existing_order(tmp_path):
    database = str(tmp_path / "target.db")

    publish_orders(
        sample_orders(), database, "batch_001", "source.csv"
    )

    updated_orders = sample_orders()
    updated_orders.loc[
        updated_orders["order_id"] == "1001", "amount"
    ] = 750.0

    result = publish_orders(
        updated_orders,
        database,
        "batch_002",
        "updated_source.csv",
    )

    with sqlite3.connect(database) as connection:
        order = connection.execute(
            "SELECT amount, batch_id FROM target_orders "
            "WHERE order_id = '1001'"
        ).fetchone()

        order_count = connection.execute(
            "SELECT COUNT(*) FROM target_orders"
        ).fetchone()[0]

    assert order == (750.0, "batch_002")
    assert order_count == 2
    assert result["new_rows"] == 0


def test_same_batch_id_with_changed_data_is_rejected(tmp_path):
    database = str(tmp_path / "target.db")
    orders = sample_orders()

    publish_orders(
        orders, database, "batch_001", "source.csv"
    )

    changed_orders = orders.copy()
    changed_orders.loc[0, "amount"] = 999.0

    with pytest.raises(ValueError, match="different content"):
        publish_orders(
            changed_orders, database, "batch_001", "source.csv"
        )


def test_duplicate_order_ids_are_rejected(tmp_path):
    database = str(tmp_path / "target.db")
    orders = sample_orders()

    duplicate_orders = pd.concat(
        [orders, orders.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        publish_orders(
            duplicate_orders, database, "batch_001", "source.csv"
        )


def test_negative_amount_is_rejected(tmp_path):
    database = str(tmp_path / "target.db")
    orders = sample_orders()
    orders.loc[0, "amount"] = -100.0

    with pytest.raises(ValueError, match="Negative"):
        publish_orders(
            orders, database, "batch_001", "source.csv"
        )


def test_failed_publish_rolls_back_and_can_be_retried(tmp_path):
    database = str(tmp_path / "target.db")

    # Seed the database with one existing order.
    publish_orders(
        sample_orders().iloc[[0]],
        database,
        "batch_initial",
        "source.csv",
    )

    # The new order is inserted first; updating the existing order
    # will then trigger a simulated database failure.
    failing_orders = pd.concat(
        [
            sample_orders().iloc[[1]],
            sample_orders().iloc[[0]],
        ],
        ignore_index=True,
    )

    with sqlite3.connect(database) as connection:
        connection.execute("""
            CREATE TRIGGER fail_order_update
            BEFORE UPDATE ON target_orders
            BEGIN
                SELECT RAISE(ABORT, 'simulated publish failure');
            END
        """)

    with pytest.raises(
        sqlite3.IntegrityError,
        match="simulated publish failure",
    ):
        publish_orders(
            failing_orders,
            database,
            "batch_retry",
            "source.csv",
        )

    # The failed transaction must leave neither the inserted order
    # nor the published-batch record behind.
    with sqlite3.connect(database) as connection:
        order_ids = {
            row[0]
            for row in connection.execute(
                "SELECT order_id FROM target_orders"
            ).fetchall()
        }

        batch = connection.execute(
            "SELECT batch_id FROM published_batches "
            "WHERE batch_id = 'batch_retry'"
        ).fetchone()

        connection.execute("DROP TRIGGER fail_order_update")

    assert order_ids == {"1001"}
    assert batch is None

    # Retrying the same batch after the simulated failure is removed
    # should publish successfully.
    result = publish_orders(
        failing_orders,
        database,
        "batch_retry",
        "source.csv",
    )

    assert result["already_published"] is False

    with sqlite3.connect(database) as connection:
        order_ids = {
            row[0]
            for row in connection.execute(
                "SELECT order_id FROM target_orders"
            ).fetchall()
        }

        published_batch = connection.execute(
            "SELECT batch_id FROM published_batches "
            "WHERE batch_id = 'batch_retry'"
        ).fetchone()

    assert order_ids == {"1001", "1002"}
    assert published_batch == ("batch_retry",)