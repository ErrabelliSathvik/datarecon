
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


def validate_orders(
    dataframe: pd.DataFrame,
    valid_customer_ids=None,
):
    """Validate orders and separate valid and rejected records.

    When valid_customer_ids is supplied, customer IDs must exist
    in that reference collection.

    Missing or unexpected columns raise ValueError because they
    indicate a schema-level problem rather than a row-level issue.
    """

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    # Check required schema columns.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Reject unexpected schema changes explicitly.
    unexpected_columns = [
        column
        for column in dataframe.columns
        if column not in REQUIRED_COLUMNS
    ]

    if unexpected_columns:
        raise ValueError(
            f"Unexpected columns: {unexpected_columns}"
        )

    original = dataframe.copy().reset_index(drop=True)
    row_count = len(original)

    # Keep the original one-based data-row number for quarantine.
    source_row_numbers = list(range(1, row_count + 1))
    working = original.copy()
    reasons = [[] for _ in range(row_count)]

    def reject(mask, reason):
        """Add a rejection reason to every matching row."""
        mask = pd.Series(mask).reset_index(drop=True)
        mask = mask.fillna(False).astype(bool)

        for position, invalid in enumerate(mask.tolist()):
            if invalid:
                reasons[position].append(reason)

    # Required values must be present and non-empty.
    for column in REQUIRED_COLUMNS:
        values = working[column].astype("string").str.strip()
        missing = (
            working[column].isna()
            | values.eq("").fillna(False)
        )
        reject(missing, f"missing_required_field:{column}")

    # Amount must be numeric and nonnegative.
    amounts = pd.to_numeric(working["amount"], errors="coerce")
    reject(amounts.isna(), "invalid_amount")
    reject(amounts.lt(0).fillna(False), "negative_amount")

    # Dates must be parseable.
    dates = pd.to_datetime(working["order_date"], errors="coerce")
    reject(dates.isna(), "invalid_order_date")

    # Normalize and validate statuses.
    statuses = (
        working["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    reject(~statuses.isin(VALID_STATUSES), "invalid_status")

    # Order IDs must be unique and non-empty.
    order_ids = working["order_id"].astype("string").str.strip()
    has_order_id = (
        order_ids.notna()
        & order_ids.ne("").fillna(False)
    )
    duplicates = order_ids.duplicated(keep=False) & has_order_id
    reject(duplicates, "duplicate_order_id")

    # Check customer references when a reference collection is supplied.
    if valid_customer_ids is not None:
        reference_ids = {
            str(customer_id).strip()
            for customer_id in valid_customer_ids
            if pd.notna(customer_id) and str(customer_id).strip()
        }

        customer_ids = (
            working["customer_id"]
            .astype("string")
            .str.strip()
        )

        unknown_customer = (
            customer_ids.notna()
            & customer_ids.ne("").fillna(False)
            & ~customer_ids.isin(reference_ids)
        )
        reject(
            unknown_customer,
            "invalid_reference_key:customer_id",
        )

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

    # Preserve original values in quarantine for traceability.
    rejected = original.iloc[rejected_positions].copy()
    rejected.insert(
        0,
        "source_row_number",
        [
            source_row_numbers[position]
            for position in rejected_positions
        ],
    )
    rejected["rejection_reason"] = [
        ";".join(reasons[position])
        for position in rejected_positions
    ]

    # Normalize records that passed all validation rules.
    valid = original.iloc[valid_positions].copy()

    valid["order_id"] = valid["order_id"].astype(str).str.strip()
    valid["customer_id"] = (
        valid["customer_id"].astype(str).str.strip()
    )
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

    return (
        valid.reset_index(drop=True),
        rejected.reset_index(drop=True),
    )
