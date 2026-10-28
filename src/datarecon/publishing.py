
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
    """Initialize target tables and the batch replay ledger."""

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
    missing = set(REQUIRED_COLUMNS) - set(dataframe.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df = dataframe[REQUIRED_COLUMNS].copy()

    if df.isna().any().any():
        raise ValueError("Publishing data contains null required values")

    df["order_id"] = df["order_id"].astype(str)
    df["customer_id"] = df["customer_id"].astype(str)
    df["order_date"] = df["order_date"].astype(str)
    df["status"] = df["status"].astype(str)

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

    # Sort by key so row order does not affect the batch fingerprint.
    return df.sort_values("order_id").reset_index(drop=True)


def _content_hash(dataframe: pd.DataFrame) -> str:
    records = dataframe.to_dict(orient="records")
    canonical = json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def publish_orders(
    dataframe: pd.DataFrame,
    database_path: str,
    batch_id: str,
    source_file: str,
) -> dict:
    """Publish a batch safely and reject reuse of its ID for changed data."""

    if not batch_id or not batch_id.strip():
        raise ValueError("batch_id must not be empty")

    if not source_file or not source_file.strip():
        raise ValueError("source_file must not be empty")

    df = _validate_and_prepare(dataframe)
    fingerprint = _content_hash(df)

    initialize_target(database_path)

    with sqlite3.connect(database_path) as connection:
        # A transaction protects the batch ledger and target writes together.
        with connection:
            previous = connection.execute(
                """
                SELECT content_hash, row_count
                FROM published_batches
                WHERE batch_id = ?
                """,
                (batch_id,),
            ).fetchone()

            if previous:
                if previous[0] != fingerprint:
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

            before_count = connection.execute(
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

            after_count = connection.execute(
                "SELECT COUNT(*) FROM target_orders"
            ).fetchone()[0]

    return {
        "batch_id": batch_id,
        "input_count": len(df),
        "target_count_before": before_count,
        "target_count_after": after_count,
        "new_rows": after_count - before_count,
        "already_published": False,
        "content_hash": fingerprint,
    }
