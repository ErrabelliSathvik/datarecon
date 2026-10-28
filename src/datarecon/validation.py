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

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

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

    # Keep the original data-row position for the rejection report.
    source_row_numbers = list(range(1, row_count + 1))
    working = original.copy()
    working["_source_row_number"] = source_row_numbers

    reasons = [[] for _ in range(row_count)]

    def reject(mask, reason):
        """Add a rejection reason to each matching row."""
        mask = pd.Series(mask).reset_index(drop=True)
        mask = mask.fillna(False).astype(bool)

        for position, invalid in enumerate(mask.tolist()):
            if invalid:
                reasons[position].append(reason)

    # Check that required fields are present.
    for column in REQUIRED_COLUMNS:
        values = working[column].astype("string").str.strip()
        missing = (
            working[column].isna()
            | values.eq("").fillna(False)
        )

        reject(missing, f"missing_required_field:{column}")

    # Check that amounts are numeric and nonnegative.
    amounts = pd.to_numeric(working["amount"], errors="coerce")

    reject(amounts.isna(), "invalid_amount")
    reject(amounts.lt(0).fillna(False), "negative_amount")

    # Check that order dates can be parsed.
    dates = pd.to_datetime(working["order_date"], errors="coerce")
    reject(dates.isna(), "invalid_order_date")

    # Normalize statuses before checking the allowed values.
    statuses = (
        working["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    reject(~statuses.isin(VALID_STATUSES), "invalid_status")

    # Order IDs must be present and unique.
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

    # Keep the original values for records that need review.
    rejected = original.iloc[rejected_positions].copy()

    rejected.insert(
        0,
        "source_row_number",
        [source_row_numbers[position] for position in rejected_positions],
    )

    rejected["rejection_reason"] = [
        ";".join(reasons[position])
        for position in rejected_positions
    ]

    # Clean up records that passed all validation checks.
    valid = original.iloc[valid_positions].copy()

    valid["order_id"] = valid["order_id"].astype(str).str.strip()
    valid["customer_id"] = valid["customer_id"].astype(str).str.strip()

    valid["order_date"] = pd.to_datetime(
        valid["order_date"],
        errors="raise",
    ).dt.strftime("%Y-%m-%d")

    valid["amount"] = pd.to_numeric(
        valid["amount"],
        errors="raise",
    )

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
