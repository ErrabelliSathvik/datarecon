
import sqlite3
from pathlib import Path


def initialize_database(database_path: str) -> None:
    """Create the run history table if it does not exist."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                source_input_count INTEGER NOT NULL DEFAULT 0,
                source_valid_count INTEGER NOT NULL DEFAULT 0,
                source_rejected_count INTEGER NOT NULL DEFAULT 0,
                target_input_count INTEGER NOT NULL DEFAULT 0,
                target_valid_count INTEGER NOT NULL DEFAULT 0,
                target_rejected_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT
            )
        """)


def record_run(database_path: str, report: dict) -> None:
    """Insert or update a pipeline run using its stable run ID."""

    initialize_database(database_path)

    validation = report.get("validation", {})

    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            INSERT INTO pipeline_runs (
                run_id, started_at, completed_at, status,
                source_input_count, source_valid_count,
                source_rejected_count, target_input_count,
                target_valid_count, target_rejected_count,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                completed_at = excluded.completed_at,
                status = excluded.status,
                source_input_count = excluded.source_input_count,
                source_valid_count = excluded.source_valid_count,
                source_rejected_count = excluded.source_rejected_count,
                target_input_count = excluded.target_input_count,
                target_valid_count = excluded.target_valid_count,
                target_rejected_count = excluded.target_rejected_count,
                error_message = excluded.error_message
        """, (
            report["run_id"],
            report["started_at"],
            report.get("completed_at"),
            report.get("status", "unknown"),
            validation.get("source_input_count", 0),
            validation.get("source_valid_count", 0),
            validation.get("source_rejected_count", 0),
            validation.get("target_input_count", 0),
            validation.get("target_valid_count", 0),
            validation.get("target_rejected_count", 0),
            report.get("error_message"),
        ))


def get_runs(database_path: str) -> list[dict]:
    """Return run history ordered by start time."""

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT * FROM pipeline_runs ORDER BY started_at DESC
        """).fetchall()

    return [dict(row) for row in rows]
