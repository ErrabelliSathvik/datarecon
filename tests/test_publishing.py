
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

    first = publish_orders(
        orders, database, "batch_001", "source.csv"
    )
    second = publish_orders(
        orders, database, "batch_001", "source.csv"
    )

    assert first["target_count_after"] == 2

    # Confirm the database contains no duplicate orders.
    with sqlite3.connect(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM target_orders"
        ).fetchone()[0]

    assert count == 2
    assert second["new_rows"] == 0
    assert second["already_published"] is True


def test_new_batch_updates_existing_order(tmp_path):
    database = str(tmp_path / "target.db")

    publish_orders(
        sample_orders(), database, "batch_001", "source.csv"
    )

    changed = sample_orders()
    changed.loc[changed["order_id"] == "1001", "amount"] = 750.0

    result = publish_orders(
        changed, database, "batch_002", "updated_source.csv"
    )

    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT amount, batch_id FROM target_orders "
            "WHERE order_id = '1001'"
        ).fetchone()

        count = connection.execute(
            "SELECT COUNT(*) FROM target_orders"
        ).fetchone()[0]

    assert row == (750.0, "batch_002")
    assert count == 2
    assert result["new_rows"] == 0


def test_same_batch_id_with_changed_data_is_rejected(tmp_path):
    database = str(tmp_path / "target.db")
    orders = sample_orders()

    publish_orders(
        orders, database, "batch_001", "source.csv"
    )

    changed = orders.copy()
    changed.loc[0, "amount"] = 999.0

    with pytest.raises(ValueError, match="different content"):
        publish_orders(
            changed, database, "batch_001", "source.csv"
        )


def test_duplicate_order_ids_are_rejected(tmp_path):
    database = str(tmp_path / "target.db")
    orders = sample_orders()

    duplicate = pd.concat(
        [orders, orders.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        publish_orders(
            duplicate, database, "batch_001", "source.csv"
        )


def test_negative_amount_is_rejected(tmp_path):
    database = str(tmp_path / "target.db")
    orders = sample_orders()
    orders.loc[0, "amount"] = -100.0

    with pytest.raises(ValueError, match="Negative"):
        publish_orders(
            orders, database, "batch_001", "source.csv"
        )
