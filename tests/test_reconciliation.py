
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
    Validate order records.

    Returns:
        valid: Normalized records suitable for publishing.
        rejected: Original input fields plus source row number
                  and one or more rejection reasons.

    Source row numbers are 1-based data-row numbers, excluding
    the CSV header.
    """
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

    # Preserve original values for quarantine and debugging.
    working = original.copy()
    working["_source_row_number"] = range(1, len(working) + 1)

    reasons = [[] for _ in range(len(working))]

    def reject(mask, reason):
        for position in range(len(working)):
            if bool(mask.iloc[position]):
                reasons[position].append(reason)

    # Required-field checks.
    for column in ["order_id", "customer_id", "order_date", "amount", "status"]:
        values = working[column].astype("string").str.strip()
        reject(
            working[column].isna() | values.eq("").fillna(False),
            f"missing_{column}",
        )

    # Amount checks.
    numeric_amount = pd.to_numeric(
        working["amount"], errors="coerce"
    )

    reject(
        numeric_amount.isna(),
        "invalid_amount",
    )

    reject(
        numeric_amount.lt(0).fillna(False),
        "negative_amount",
    )

    # Date checks.
    parsed_dates = pd.to_datetime(
        working["order_date"], errors="coerce"
    )

    reject(
        parsed_dates.isna(),
        "invalid_order_date",
    )

    # Status checks.
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

    # Reject every occurrence of a duplicate non-empty business key.
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

    rejected_mask = pd.Series(
        [bool(row_reasons) for row_reasons in reasons],
        index=working.index,
    )

    # Quarantine retains the original fields and adds audit metadata.
    rejected = original.loc[rejected_mask].copy()
    rejected.insert(
        0,
        "source_row_number",
        working.loc[rejected_mask, "_source_row_number"].tolist(),
    )
    rejected["rejection_reason"] = [
        ";".join(reasons[position])
        for position in range(len(reasons))
        if reasons[position]
    ]

    # Only clean records proceed to publishing.
    valid = working.loc[~rejected_mask, original_columns].copy()

    valid["order_id"] = valid["order_id"].astype(str).str.strip()
    valid["customer_id"] = valid["customer_id"].astype(str).str.strip()
    valid["order_date"] = pd.to_datetime(
        valid["order_date"]
    ).dt.strftime("%Y-%m-%d")
    valid["amount"] = pd.to_numeric(valid["amount"])
    valid["status"] = (
        valid["status"].astype(str).str.strip().str.lower()
    )

    return valid.reset_index(drop=True), rejected.reset_index(drop=True)
