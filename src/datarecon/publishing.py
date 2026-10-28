import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "amount",
    "status",
]


def initialize_target(database_path: str) -> None:
    """Create the database tables if they do not exist."""

    Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS target_orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_date TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                status TEXT NOT NULL,
                batch_id TEXT NOT NULL,
                source_file TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS published_batches (
                batch_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _validate_and_prepare(dataframe: pd.DataFrame) -> pd.DataFrame:
    missing_columns = set(REQUIRED_COLUMNS) - set(dataframe.columns)
    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )

    df = dataframe[REQUIRED_COLUMNS].copy()

    if df.isna().any().any():
        raise ValueError("Publishing data contains null required values")

    for column in ["order_id", "customer_id", "order_date", "status"]:
        df[column] = df[column].astype(str)

    if df["order_id"].str.strip().eq("").any():
        raise ValueError("order_id cannot be empty")

    if df["order_id"].duplicated().any():
        raise ValueError("Duplicate order_id in publishing batch")

    amounts = pd.to_numeric(df["amount"], errors="coerce")

    if amounts.isna().any():
        raise ValueError("Publishing data contains invalid amounts")

    if (amounts < 0).any():
        raise ValueError("Negative order amount")

    df["amount"] = amounts.astype(float)

    # Keep the hash consistent even if rows arrive in a different order.
    return df.sort_values("order_id").reset_index(drop=True)


def _content_hash(dataframe: pd.DataFrame) -> str:
    records = dataframe.to_dict(orient="records")
    content = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def publish_orders(
    dataframe: pd.DataFrame,
    database_path: str,
    batch_id: str,
    source_file: str,
) -> dict:
    """Publish orders and prevent changed data from reusing a batch ID."""

    if not batch_id or not batch_id.strip():
        raise ValueError("batch_id must not be empty")

    if not source_file or not source_file.strip():
        raise ValueError("source_file must not be empty")

    df = _validate_and_prepare(dataframe)
    fingerprint = _content_hash(df)

    initialize_target(database_path)

    with sqlite3.connect(database_path) as connection:
        with connection:
            previous_batch = connection.execute(
                """
                SELECT content_hash, row_count
                FROM published_batches
                WHERE batch_id = ?
                """,
                (batch_id,),
            ).fetchone()

            if previous_batch:
                if previous_batch[0] != fingerprint:
                    raise ValueError(
                        f"Batch ID '{batch_id}' was already used "
                        "with different content"
                    )

                return {
                    "batch_id": batch_id,
                    "input_count": len(df),
                    "new_rows": 0,
                    "already_published": True,
                    "content_hash": fingerprint,
                }

            count_before = connection.execute(
                "SELECT COUNT(*) FROM target_orders"
            ).fetchone()[0]

            connection.executemany(
                """
                INSERT INTO target_orders (
                    order_id, customer_id, order_date, amount,
                    status, batch_id, source_file
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_id) DO UPDATE SET
                    customer_id = excluded.customer_id,
                    order_date = excluded.order_date,
                    amount = excluded.amount,
                    status = excluded.status,
                    batch_id = excluded.batch_id,
                    source_file = excluded.source_file
                """,
                [
                    (
                        row.order_id,
                        row.customer_id,
                        row.order_date,
                        row.amount,
                        row.status,
                        batch_id,
                        source_file,
                    )
                    for row in df.itertuples(index=False)
                ],
            )

            connection.execute(
                """
                INSERT INTO published_batches (
                    batch_id, content_hash, row_count
                )
                VALUES (?, ?, ?)
                """,
                (batch_id, fingerprint, len(df)),
            )

            count_after = connection.execute(
                "SELECT COUNT(*) FROM target_orders"
            ).fetchone()[0]

    return {
        "batch_id": batch_id,
        "input_count": len(df),
        "target_count_before": count_before,
        "target_count_after": count_after,
        "new_rows": count_after - count_before,
        "already_published": False,
        "content_hash": fingerprint,
    }
