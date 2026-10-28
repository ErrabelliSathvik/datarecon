import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from datarecon.publishing import publish_orders
from datarecon.reconciliation import reconcile
from datarecon.run_history import record_run
from datarecon.validation import validate_orders


def main():
    parser = argparse.ArgumentParser(
        description="Validate, compare, and publish order data."
    )
    parser.add_argument(
        "--source",
        default="data/sample/source_orders.csv",
    )
    parser.add_argument(
        "--target",
        default="data/sample/target_orders.csv",
    )
    parser.add_argument(
        "--output",
        default="outputs/sample",
    )
    parser.add_argument(
        "--database",
        default="outputs/datarecon.db",
    )
    parser.add_argument(
        "--batch-id",
        required=True,
        help="Identifier for the input batch.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%S%fZ")

    report = {
        "run_id": run_id,
        "batch_id": args.batch_id,
        "started_at": started_at.isoformat(),
        "completed_at": None,
        "status": "failed",
        "error_message": None,
    }

    try:
        source_input = pd.read_csv(args.source)
        target_input = pd.read_csv(args.target)

        source_valid, source_rejects = validate_orders(source_input)
        target_valid, target_rejects = validate_orders(target_input)

        source_rejects.to_csv(
            output_dir / "source_rejects.csv",
            index=False,
        )
        target_rejects.to_csv(
            output_dir / "target_rejects.csv",
            index=False,
        )

        # Compare only records that passed validation.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            source_clean = temp_dir / "source.csv"
            target_clean = temp_dir / "target.csv"

            source_valid.to_csv(source_clean, index=False)
            target_valid.to_csv(target_clean, index=False)

            reconciliation = reconcile(
                str(source_clean),
                str(target_clean),
                str(output_dir),
            )

        report.update(reconciliation)
        report["run_id"] = run_id
        report["batch_id"] = args.batch_id
        report["started_at"] = started_at.isoformat()

        report["validation"] = {
            "source_input_count": len(source_input),
            "source_valid_count": len(source_valid),
            "source_rejected_count": len(source_rejects),
            "target_input_count": len(target_input),
            "target_valid_count": len(target_valid),
            "target_rejected_count": len(target_rejects),
        }

        # Publish the valid source records to SQLite.
        report["publishing"] = publish_orders(
            dataframe=source_valid,
            database_path=args.database,
            batch_id=args.batch_id,
            source_file=str(Path(args.source)),
        )

        has_rejects = (
            not source_rejects.empty
            or not target_rejects.empty
        )

        if has_rejects:
            report["status"] = "completed_with_data_quality_issues"
            report["reconciliation"]["matched"] = False
        else:
            report["status"] = "completed"

    except Exception as exc:
        report["status"] = "failed"
        report["error_message"] = f"{type(exc).__name__}: {exc}"

    report["completed_at"] = datetime.now(timezone.utc).isoformat()

    report_path = output_dir / "reconciliation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    record_run(args.database, report)
    print(json.dumps(report, indent=2))

    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
