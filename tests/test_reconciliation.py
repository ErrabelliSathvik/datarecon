import pandas as pd


REQUIRED_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "amount",
    "status",
]

VALID_STATUSES = {
    "pending",
    "completed",
    "shipped",
    "cancelled",
}


def validate_orders(dataframe: pd.DataFrame):
    """Separate valid orders from records that fail validation."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    original = dataframe.copy().reset_index(drop=True)
    original_columns = list(original.columns)
    row_count = len(original)

    # Keep the original row numbers for rejected records.
    working = original.copy()
    working["_source_row_number"] = range(1, row_count + 1)
    reasons = [[] for _ in range(row_count)]

    def reject(mask, reason):
        """Record why each matching row failed validation."""
        mask = pd.Series(mask).reset_index(drop=True)
        mask = mask.fillna(False).astype(bool)

        for position, invalid in enumerate(mask):
            if invalid:
                reasons[position].append(reason)

    # Check required fields.
    for column in REQUIRED_COLUMNS:
        values = working[column].astype("string").str.strip()
        missing = (
            working[column].isna()
            | values.eq("").fillna(False)
        )
        reject(missing, f"missing_{column}")

    # Check amounts.
    amounts = pd.to_numeric(working["amount"], errors="coerce")
    reject(amounts.isna(), "invalid_amount")
    reject(amounts.lt(0).fillna(False), "negative_amount")

    # Check order dates.
    dates = pd.to_datetime(working["order_date"], errors="coerce")
    reject(dates.isna(), "invalid_order_date")

    # Check order statuses.
    statuses = (
        working["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    reject(~statuses.isin(VALID_STATUSES), "invalid_status")

    # Reject all occurrences of duplicate, non-empty order IDs.
    order_ids = working["order_id"].astype("string").str.strip()
    has_order_id = (
        order_ids.notna()
        & order_ids.ne("").fillna(False)
    )
    duplicates = order_ids.duplicated(keep=False) & has_order_id
    reject(duplicates, "duplicate_order_id")

    rejected_positions = [
        position
        for position, row_reasons in enumerate(reasons)
        if row_reasons
    ]
    valid_positions = [
        position
        for position, row_reasons in enumerate(reasons)
        if not row_reasons
    ]

    # Keep original values in the rejection output.
    rejected = original.iloc[rejected_positions].copy()
    rejected.insert(
        0,
        "source_row_number",
        [position + 1 for position in rejected_positions],
    )
    rejected["rejection_reason"] = [
        ";".join(reasons[position])
        for position in rejected_positions
    ]

    # Normalize records that passed validation.
    valid = original.iloc[valid_positions].copy()

    valid["order_id"] = valid["order_id"].astype(str).str.strip()
    valid["customer_id"] = valid["customer_id"].astype(str).str.strip()
    valid["order_date"] = pd.to_datetime(
        valid["order_date"],
        errors="raise",
    ).dt.strftime("%Y-%m-%d")
    valid["amount"] = pd.to_numeric(valid["amount"], errors="raise")
    valid["status"] = (
        valid["status"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    valid = valid[original_columns]

    return (
        valid.reset_index(drop=True),
        rejected.reset_index(drop=True),
    )
