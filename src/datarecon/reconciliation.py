
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


KEY_COLUMN = "order_id"

COMPARE_COLUMNS = [
    "customer_id",
    "order_date",
    "amount",
    "status",
]


def reconcile(
    source_path: str,
    target_path: str,
    output_dir: str,
) -> dict:
    """Compare source and target orders and save reconciliation outputs."""

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    started_at = datetime.now(timezone.utc)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(source_path)
    target = pd.read_csv(target_path)

    required_columns = [KEY_COLUMN, *COMPARE_COLUMNS]

    for name, dataframe in [("source", source), ("target", target)]:
        missing = set(required_columns) - set(dataframe.columns)
        if missing:
            raise ValueError(
                f"{name} dataset is missing columns: {sorted(missing)}"
            )

    # A primary key must exist and be unique.
    for name, dataframe in [("source", source), ("target", target)]:
        if dataframe[KEY_COLUMN].isna().any():
            raise ValueError(f"{name} contains null order_id values")

        if dataframe[KEY_COLUMN].duplicated().any():
            raise ValueError(f"{name} contains duplicate order_id values")

    source = source.set_index(KEY_COLUMN, drop=False)
    target = target.set_index(KEY_COLUMN, drop=False)

    source_keys = set(source.index)
    target_keys = set(target.index)

    source_only_keys = sorted(source_keys - target_keys)
    target_only_keys = sorted(target_keys - source_keys)
    common_keys = sorted(source_keys & target_keys)

    mismatches = []

    for key in common_keys:
        for column in COMPARE_COLUMNS:
            source_value = source.at[key, column]
            target_value = target.at[key, column]

            # Treat two missing values as equal.
            if pd.isna(source_value) and pd.isna(target_value):
                continue

            # Numeric amounts must be compared numerically.
            if column == "amount":
                equal = (
                    pd.notna(source_value)
                    and pd.notna(target_value)
                    and float(source_value) == float(target_value)
                )
            else:
                equal = (
                    pd.notna(source_value)
                    and pd.notna(target_value)
                    and str(source_value) == str(target_value)
                )

            if not equal:
                mismatches.append({
                    "order_id": str(key),
                    "column": column,
                    "source_value": (
                        None if pd.isna(source_value) else str(source_value)
                    ),
                    "target_value": (
                        None if pd.isna(target_value) else str(target_value)
                    ),
                })

    # Aggregate only records whose business keys exist in both datasets.
    source_common = source.loc[common_keys]
    target_common = target.loc[common_keys]

    source_amount = float(source_common["amount"].sum())
    target_amount = float(target_common["amount"].sum())

    report = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "source": {
            "row_count": len(source),
            "total_amount": float(source["amount"].sum()),
        },
        "target": {
            "row_count": len(target),
            "total_amount": float(target["amount"].sum()),
        },
        "reconciliation": {
            "row_count_difference": len(source) - len(target),
            "source_only_count": len(source_only_keys),
            "target_only_count": len(target_only_keys),
            "field_mismatch_count": len(mismatches),
            "common_key_count": len(common_keys),
            "common_key_source_amount": source_amount,
            "common_key_target_amount": target_amount,
            "common_key_amount_difference": (
                source_amount - target_amount
            ),
            "matched": (
                not source_only_keys
                and not target_only_keys
                and not mismatches
            ),
        },
    }

    (output / "reconciliation_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    pd.DataFrame(
        {"order_id": source_only_keys}
    ).to_csv(output / "source_only.csv", index=False)

    pd.DataFrame(
        {"order_id": target_only_keys}
    ).to_csv(output / "target_only.csv", index=False)

    pd.DataFrame(
        mismatches,
        columns=[
            "order_id",
            "column",
            "source_value",
            "target_value",
        ],
    ).to_csv(output / "field_mismatches.csv", index=False)

    return report
