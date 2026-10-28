
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
    """
    Validate and normalize order records.

    Returns:
        valid: Clean, normalized records.
        rejected: Original input fields with source_row_number
                  and rejection_reason.

    Row numbers are 1-based data-row numbers, excluding the header.
    """

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

    # Reset the index to ensure positional alignment.
    original = dataframe.copy().reset_index(drop=True)
    original_columns = list(original.columns)
    row_count = len(original)

    # Explicitly assign 1-based data-row numbers.
    source_row_numbers = list(range(1, row_count + 1))

    working = original.copy()
    working["_source_row_number"] = source_row_numbers

    reasons = [[] for _ in range(row_count)]

    def reject(mask, reason):
        """Record a reason for each invalid row."""
        mask = pd.Series(mask).reset_index(drop=True)
        mask = mask.fillna(False).astype(bool)

        for position, invalid in enumerate(mask.tolist()):
            if invalid:
                reasons[position].append(reason)

    # 1. Required-field validation.
    for column in REQUIRED_COLUMNS:
        values = working[column].astype("string").str.strip()

        missing = (
            working[column].isna()
            | values.eq("").fillna(False)
        )

        reject(
            missing,
            f"missing_required_field:{column}",
        )

    # 2. Amount validation.
    numeric_amount = pd.to_numeric(
        working["amount"],
        errors="coerce",
    )

    reject(
        numeric_amount.isna(),
        "invalid_amount",
    )

    reject(
        numeric_amount.lt(0).fillna(False),
        "negative_amount",
    )

    # 3. Date validation.
    parsed_dates = pd.to_datetime(
        working["order_date"],
        errors="coerce",
    )

    reject(
        parsed_dates.isna(),
        "invalid_order_date",
    )

    # 4. Status validation.
    normalized_status = (
        working["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    reject(
        ~normalized_status.isin(VALID_STATUSES),
        "invalid_status",
    )

    # 5. Business-key validation.
    normalized_key = (
        working["order_id"]
        .astype("string")
        .str.strip()
    )

    nonempty_key = (
        normalized_key.notna()
        & normalized_key.ne("").fillna(False)
    )

    duplicate_key = (
        normalized_key.duplicated(keep=False)
        & nonempty_key
    )

    reject(
        duplicate_key,
        "duplicate_order_id",
    )

    # 6. Separate valid and rejected records by position.
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

    # Quarantine retains original field values.
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

    # Normalize only valid records.
    valid = original.iloc[valid_positions].copy()

    valid["order_id"] = (
        valid["order_id"].astype(str).str.strip()
    )

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

    valid = valid[original_columns]

    return (
        valid.reset_index(drop=True),
        rejected.reset_index(drop=True),
    )
