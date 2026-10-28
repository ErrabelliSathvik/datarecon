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
    """Compare two order datasets and save the results."""

    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%S%fZ")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(source_path)
    target = pd.read_csv(target_path)

    required_columns = [KEY_COLUMN, *COMPARE_COLUMNS]

    for name, dataframe in [("source", source), ("target", target)]:
        missing_columns = set(required_columns) - set(dataframe.columns)

        if missing_columns:
            raise ValueError(
                f"{name} dataset is missing columns: "
                f"{sorted(missing_columns)}"
            )

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

    for order_id in common_keys:
        for column in COMPARE_COLUMNS:
            source_value = source.at[order_id, column]
            target_value = target.at[order_id, column]

            # Two missing values are treated as equal.
            if pd.isna(source_value) and pd.isna(target_value):
                continue

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
                    "order_id": str(order_id),
                    "column": column,
                    "source_value": (
                        None if pd.isna(source_value) else str(source_value)
                    ),
                    "target_value": (
                        None if pd.isna(target_value) else str(target_value)
                    ),
                })

    # Compare totals for orders present in both datasets.
    source_common = source.loc[common_keys]
    target_common = target.loc[common_keys]

    source_common_amount = float(source_common["amount"].sum())
    target_common_amount = float(target_common["amount"].sum())

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
            "common_key_source_amount": source_common_amount,
            "common_key_target_amount": target_common_amount,
            "common_key_amount_difference": (
                source_common_amount - target_common_amount
            ),
            "matched": (
                not source_only_keys
                and not target_only_keys
                and not mismatches
            ),
        },
    }

    (output_dir / "reconciliation_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    pd.DataFrame({"order_id": source_only_keys}).to_csv(
        output_dir / "source_only.csv",
        index=False,
    )

    pd.DataFrame({"order_id": target_only_keys}).to_csv(
        output_dir / "target_only.csv",
        index=False,
    )

    pd.DataFrame(
        mismatches,
        columns=[
            "order_id",
            "column",
            "source_value",
            "target_value",
        ],
    ).to_csv(output_dir / "field_mismatches.csv", index=False)

    return report
