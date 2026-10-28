# Data Dictionary

## Orders

Each row represents one order, identified by its `order_id`.

| Column | Type | Required | Description |
|---|---|---|---|
| `order_id` | String | Yes | Unique identifier for an order |
| `customer_id` | String | Yes | ID of the customer who placed the order |
| `order_date` | ISO date | Yes | Date when the order was placed |
| `amount` | Decimal | Yes | Order amount, which cannot be negative |
| `status` | String | Yes | Current status: `pending`, `completed`, `shipped`, or `cancelled` |

## Validation Rules

Before comparing the datasets, DataRecon checks that:

- Every order has an `order_id`, and the ID is unique within its dataset.
- `customer_id` is provided.
- `order_date` contains a valid date.
- `amount` is numeric and is not negative.
- `status` is one of the supported values listed above.

Records are matched between the source and target using `order_id`. For orders found in both datasets, DataRecon compares the other fields to identify differences.

## Reconciliation Results

The reconciliation report contains the following fields.

| Field | Description |
|---|---|
| `run_id` | Unique ID for the pipeline execution |
| `row_count_difference` | Difference between source and target row counts |
| `source_only_count` | Number of orders found only in the source |
| `target_only_count` | Number of orders found only in the target |
| `field_mismatch_count` | Number of field comparisons that differ |
| `common_key_count` | Number of order IDs present in both datasets |
| `matched` | Indicates whether the compared records reconcile successfully |

## Database Tables

The SQLite `target_orders` table stores order details along with the `batch_id` and `source_file` used during publishing.

The `pipeline_runs` table keeps a record of pipeline executions, including their status, timestamps, and validation counts.

## Assumptions and Limitations

- Customer IDs are checked for presence, but they are not validated against a separate customer master dataset.
- Amount calculations currently use floating-point values. Decimal arithmetic or integer values in minor currency units would be more suitable when exact financial precision is required.
- Quarantined records do not yet preserve the complete original source row in every case.
- When an existing order changes, the target table is updated rather than keeping a separate history of previous versions.
