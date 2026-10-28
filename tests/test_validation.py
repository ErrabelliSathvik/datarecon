
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
    assert "negative_amount" in rejected.iloc[0]["rejection_reason"] or (
        "negative_amount" in ";".join(rejected["rejection_reason"])
    )
    assert "invalid_status" in ";".join(rejected["rejection_reason"])


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
