
import pandas as pd

from datarecon.validation import validate_orders


COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "amount",
    "status",
]


def test_empty_dataset_is_valid_empty_input():
    data = pd.DataFrame(columns=COLUMNS)

    valid, rejected = validate_orders(data)

    assert valid.empty
    assert rejected.empty


def test_missing_required_value_is_quarantined():
    data = pd.DataFrame([
        {
            "order_id": 1001,
            "customer_id": None,
            "order_date": "2026-10-25",
            "amount": 500,
            "status": "completed",
        },
        {
            "order_id": 1002,
            "customer_id": "C002",
            "order_date": "2026-10-25",
            "amount": 600,
            "status": "completed",
        },
    ])

    valid, rejected = validate_orders(data)

    assert len(valid) == 1
    assert len(rejected) == 1
    assert (
        "missing_required_field:customer_id"
        in rejected.iloc[0]["rejection_reason"]
    )


def test_malformed_amount_is_quarantined():
    data = pd.DataFrame([
        {
            "order_id": 1001,
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": "not-a-number",
            "status": "completed",
        }
    ])

    valid, rejected = validate_orders(data)

    assert valid.empty
    assert len(rejected) == 1
    assert "invalid_amount" in rejected.iloc[0]["rejection_reason"]


def test_zero_amount_order_is_valid():
    """A zero-value order is allowed by the nonnegative amount rule."""
    data = pd.DataFrame([
        {
            "order_id": "O_ZERO",
            "customer_id": "C001",
            "order_date": "2026-10-25",
            "amount": 0,
            "status": "pending",
        }
    ])

    valid, rejected = validate_orders(data)

    assert len(valid) == 1
    assert rejected.empty
    assert valid.iloc[0]["amount"] == 0
