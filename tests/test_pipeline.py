
import json

import pandas as pd
import pytest

from datarecon.pipeline import main, load_customer_reference


def test_pipeline_quarantines_invalid_customer_reference(
    tmp_path, monkeypatch
):
    source = pd.DataFrame([
        {
            "order_id": "O1001",
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": 500,
            "status": "completed",
        },
    ])

    target = pd.DataFrame([
        {
            "order_id": "O1001",
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": 500,
            "status": "completed",
        },
        {
            "order_id": "O1002",
            "customer_id": "C999",
            "order_date": "2026-10-26",
            "amount": 250,
            "status": "pending",
        },
    ])

    source_path = tmp_path / "source.csv"
    target_path = tmp_path / "target.csv"
    customers_path = tmp_path / "customers.csv"
    output_dir = tmp_path / "output"
    database_path = tmp_path / "datarecon.db"

    source.to_csv(source_path, index=False)
    target.to_csv(target_path, index=False)

    pd.DataFrame({
        "customer_id": ["C001"],
    }).to_csv(customers_path, index=False)

    monkeypatch.setattr(
        "sys.argv",
        [
            "datarecon",
            "--source", str(source_path),
            "--target", str(target_path),
            "--customers", str(customers_path),
            "--output", str(output_dir),
            "--database", str(database_path),
            "--batch-id", "pipeline-reference-test",
        ],
    )

    main()

    report = json.loads(
        (output_dir / "reconciliation_report.json").read_text(
            encoding="utf-8"
        )
    )
    rejects = pd.read_csv(output_dir / "target_rejects.csv")

    assert report["status"] == "completed_with_data_quality_issues"
    assert report["validation"]["target_rejected_count"] == 1
    assert rejects.iloc[0]["customer_id"] == "C999"
    assert (
        rejects.iloc[0]["rejection_reason"]
        == "invalid_reference_key:customer_id"
    )


def test_rejects_duplicate_customer_reference_ids(tmp_path):
    customers_path = tmp_path / "customers.csv"

    pd.DataFrame({
        "customer_id": ["C001", "C001"],
    }).to_csv(customers_path, index=False)

    with pytest.raises(ValueError, match="duplicate customer IDs"):
        load_customer_reference(customers_path)
