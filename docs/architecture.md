# DataRecon Architecture

## Overview

DataRecon compares two order datasets and reports the differences between them. It is a local Python application that reads CSV files, processes the data with pandas, and uses SQLite for persistent storage.

I separated validation, reconciliation, publishing, and run-history tracking into different modules. This keeps the code organized and makes it easier to test each part independently.

## How the pipeline works

1. Read the source and target CSV files.
2. Validate both datasets against the expected order fields.
3. Separate invalid records and retain their rejection reasons.
4. Compare the validated datasets using `order_id`.
5. Generate a JSON reconciliation report and CSV files containing discrepancies.
6. Publish valid source records to SQLite.
7. Record the pipeline outcome in the run-history database.

The exact execution order and error-handling behavior are defined by the implementation in `src/datarecon/pipeline.py`.

## Main components

### `validation.py`

Checks required fields, amounts, dates, statuses, and duplicate order IDs. Valid records are normalized before publishing. Invalid records are returned separately with source-row information and rejection reasons.

### `reconciliation.py`

Compares source and target records using `order_id` as the business key. It identifies records found only in the source, records found only in the target, and field-level differences between records with matching keys.

It also reports row counts and amount aggregates. Equal row counts do not necessarily mean that the datasets contain the same records or values.

### `publishing.py`

Writes validated source records to SQLite. It uses `order_id` to identify existing orders and supports updating them with a later batch.

The publishing logic also records batch IDs and content hashes. This allows it to distinguish an identical batch replay from an attempt to reuse a batch ID with different data.

### `run_history.py`

Stores pipeline execution information in SQLite, including run status, timestamps, counts, and error information.

### Supporting scripts

- `generate_data.py` creates synthetic order datasets using a configurable random seed.
- `benchmark.py` measures reconciliation runtime and records performance metrics.
- `show_runs.py` displays saved run-history records.

## Data flow

```text
Source CSV ------------------+
                             |
                             v
                        Validation
                             |
                  +----------+----------+
                  |                     |
             Valid records          Rejected records
                  |                     |
                  v                     v
            Reconciliation        Quarantine CSVs
                  |
                  v
       JSON report and discrepancy CSVs

Validated source records
          |
          v
     SQLite publishing
          |
          v
     Published orders

Pipeline execution
          |
          v
       Run history
```

## Technology choices

**Python and pandas:** I used Python for the pipeline logic and pandas for reading, validating, and comparing tabular data.

**CSV:** CSV files make the input data and generated reports easy to inspect without requiring an external service.

**SQLite:** SQLite provides persistent storage without a separate database server. It suits this local project, although a larger multi-user deployment might require a different database.

**pytest:** Automated tests cover validation, reconciliation, edge cases, and publishing behavior.


## Reliability considerations

The project includes duplicate order-key validation, optional customer
referential-integrity checks, invalid-record quarantine, batch replay
protection, and automated tests.

When a customer reference file is supplied with `--customers`, the pipeline
validates customer IDs in both source and target datasets. Unknown customer
references are quarantined before reconciliation. Missing or duplicate
customer IDs in the reference file cause the run to fail.

Missing or unexpected order columns are treated as schema-level errors.
Unexpected columns are rejected explicitly rather than silently ignored.

Publishing uses database transactions. Automated tests verify that a failed
publishing operation rolls back its database changes and can be retried.

These tests do not establish complete end-to-end recovery for every possible
pipeline failure. Failures between reconciliation output, database publishing,
and run-history recording may require additional recovery handling. This
limitation should be considered before production use.

## Benchmark observations

I ran the benchmark twice using 100,000 source rows and 100,000 target rows.

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Runtime | 39.6711 seconds | 28.2016 seconds |
| Source-row throughput | 2,520.73 rows/second | 3,545.90 rows/second |
| Peak traced Python memory | 37.64 MB | 37.64 MB |
| Source-only records | 1 | 1 |
| Target-only records | 1 | 1 |
| Field mismatches | 1 | 1 |

Both runs detected one source-only record, one target-only record, and one field mismatch. The reconciliation result was `matched: false`, even though both datasets had the same number of rows.

These measurements come from local runs on Windows. Runtime and throughput varied between runs, so they should be treated as observations rather than guaranteed performance. Traced Python memory does not represent the entire process's memory usage.

## Limitations and possible improvements

DataRecon currently focuses on local batch processing. Pandas may consume more memory as datasets grow, and CSV parsing errors may need to be handled before record-level validation begins.

Possible improvements include processing large files in chunks, adding structured logging, making schemas and business rules configurable, improving recovery handling, and running more benchmarks to establish a reliable performance baseline.