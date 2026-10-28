
import pandas as pd
import pytest

from datarecon.validation import validate_orders


def test_quarantines_invalid_orders():
    data = pd.DataFrame([
        {
            "order_id": 1001,
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": 500,
            "status": "completed",
        },
        {
            "order_id": 1002,
            "customer_id": "C002",
            "order_date": "2026-10-25",
            "amount": -100,
            "status": "completed",
        },
        {
            "order_id": 1003,
            "customer_id": "C003",
            "order_date": "2026-10-25",
            "amount": 250,
            "status": "unknown",
        },
    ])

    valid, rejected = validate_orders(data)

    assert len(valid) == 1
    assert len(rejected) == 2

    rejection_reasons = ";".join(rejected["rejection_reason"])
    assert "negative_amount" in rejection_reasons
    assert "invalid_status" in rejection_reasons


def test_rejects_missing_schema_column():
    data = pd.DataFrame([
        {
            "order_id": 1001,
            "customer_id": "C001",
            "amount": 500,
            "status": "completed",
        }
    ])

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_orders(data)


def test_quarantines_orders_with_invalid_customer_reference():
    data = pd.DataFrame([
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
            "order_date": "2026-10-25",
            "amount": 250,
            "status": "pending",
        },
    ])

    valid, rejected = validate_orders(
        data,
        valid_customer_ids={"C001", "C002"},
    )

    assert valid["order_id"].tolist() == ["O1001"]
    assert rejected["order_id"].tolist() == ["O1002"]
    assert (
        rejected.iloc[0]["rejection_reason"]
        == "invalid_reference_key:customer_id"
    )


def test_rejects_unexpected_schema_column():
    data = pd.DataFrame([
        {
            "order_id": "O1001",
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": 500,
            "status": "completed",
            "unexpected_field": "unexpected",
        }
    ])

    with pytest.raises(ValueError, match="Unexpected columns"):
        validate_orders(data)
