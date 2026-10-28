# DataRecon Data Dictionary

## 1. Order input fields

The source and target datasets use the same expected order schema.

| Field | Expected meaning | Validation |
|---|---|---|
| `order_id` | Unique identifier for an order | Required; duplicate non-empty keys are rejected |
| `customer_id` | Identifier of the customer associated with the order | Required |
| `order_date` | Date associated with the order | Required; must be parseable as a date |
| `amount` | Monetary amount for the order | Required; must be numeric and non-negative |
| `status` | Current order status | Required; normalized to lowercase |

### Allowed statuses

The current validator accepts:

- `pending`
- `completed`
- `shipped`
- `cancelled`

Values are trimmed and normalized to lowercase before they are used in the valid dataset.

## 2. Business key

`order_id` is the business key used to compare source and target records.

The reconciliation logic uses this key to identify records that appear in only one dataset and to compare fields for records that share a key.

Duplicate non-empty order IDs are treated as invalid during validation. The validator rejects every occurrence of a duplicated key rather than choosing one record arbitrarily.

## 3. Validation and quarantine fields

Rejected records retain their original input fields and include additional diagnostic information.

| Field | Meaning |
|---|---|
| `source_row_number` | One-based data-row number from the input, excluding the header |
| `rejection_reason` | One or more validation reasons associated with the rejected record |

Examples of rejection reasons include:

- `missing_required_field:customer_id`
- `invalid_amount`
- `negative_amount`
- `invalid_order_date`
- `invalid_status`
- `duplicate_order_id`

A record can have more than one rejection reason. Reasons are joined with semicolons.

## 4. Reconciliation report

The JSON report summarizes the comparison between the source and target datasets.

| Field | Meaning |
|---|---|
| `source.row_count` | Number of source records included in reconciliation |
| `source.total_amount` | Sum of source amounts |
| `target.row_count` | Number of target records included in reconciliation |
| `target.total_amount` | Sum of target amounts |
| `reconciliation.row_count_difference` | Source row count minus target row count |
| `reconciliation.source_only_count` | Number of records found only in the source |
| `reconciliation.target_only_count` | Number of records found only in the target |
| `reconciliation.field_mismatch_count` | Number of field-level mismatches reported |
| `reconciliation.common_key_count` | Number of business keys shared by both datasets |
| `reconciliation.common_key_source_amount` | Source amount total for shared keys |
| `reconciliation.common_key_target_amount` | Target amount total for shared keys |
| `reconciliation.common_key_amount_difference` | Source shared-key amount minus target shared-key amount |
| `reconciliation.matched` | Indicates whether the implemented reconciliation checks found differences |

The exact report structure is defined by `src/datarecon/reconciliation.py`. If the report schema changes, this document should be updated to match it.

## 5. Discrepancy output files

| File | Purpose |
|---|---|
| `source_only.csv` | Source records without a matching target business key |
| `target_only.csv` | Target records without a matching source business key |
| `field_mismatches.csv` | Field-level differences for shared business keys |
| `source_rejects.csv` | Invalid source records |
| `target_rejects.csv` | Invalid target records |

The files are generated in the configured output directory. Their exact columns depend on the corresponding implementation.

## 6. Publishing and run history

The SQLite database stores published order records and pipeline execution history.

The publishing schema includes fields used to identify orders and track the batch associated with a published record. The batch ledger stores batch identifiers, content hashes, row counts, and publication timestamps.

The run-history table records execution status, timestamps, input and output counts, and error details. See `publishing.py` and `run_history.py` for the authoritative database schemas.

## 7. Benchmark metrics

| Metric | Meaning |
|---|---|
| `elapsed_seconds` | Total elapsed time measured by the benchmark |
| `source_rows_per_second` | Source row count divided by elapsed time |
| `peak_traced_python_memory_mb` | Peak Python memory recorded by `tracemalloc`, in megabytes |
| `reconciliation_matched` | Whether the reconciliation result reported a match |

Two local benchmark runs were recorded using 100,000 source rows and 100,000 target rows.

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Runtime | 39.6711 seconds | 28.2016 seconds |
| Source-row throughput | 2,520.73 rows/second | 3,545.90 rows/second |
| Peak traced Python memory | 37.64 MB | 37.64 MB |

Both runs reported one source-only record, one target-only record, and one field mismatch. The reconciliation result was `matched: false`.

These measurements were collected locally on Windows. Runtime varied between runs, so they should be treated as observations rather than guaranteed performance. Traced Python memory does not represent total process memory.