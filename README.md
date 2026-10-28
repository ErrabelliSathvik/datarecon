# DataRecon — Data Reconciliation Pipeline

## Overview

DataRecon is a Python batch-processing project that compares source and target order datasets to identify missing records, field-level mismatches, and invalid data. It uses business-key matching and aggregate checks rather than relying on row counts alone.

The pipeline validates CSV input, quarantines rejected records with traceable reasons, generates machine-readable reconciliation reports, and publishes valid source records to SQLite.

## Features

- Match source and target orders using `order_id`.
- Identify source-only and target-only records.
- Detect field-level differences between matching records.
- Validate required fields, amounts, dates, statuses, and duplicate order IDs.
- Reject missing or unexpected schema columns.
- Optionally validate customer references using a customer master CSV.
- Quarantine invalid records with rejection reasons.
- Publish validated source orders to SQLite.
- Protect against duplicate batch publishing and reuse of a batch ID with changed data.
- Record pipeline execution history and status.
- Generate reproducible synthetic datasets.
- Run automated tests and performance benchmarks.

## Technologies

- Python
- pandas
- NumPy
- SQLite
- pytest

## Setup

Run the following commands from the project root on Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
set PYTHONPATH=src
```

## Run Tests

```bat
python -m pytest -v
```

## Generate Test Data

Generate reproducible source and target datasets containing 100,000 rows each:

```bat
python scripts\generate_data.py --rows 100000 --seed 42
```

The fixed random seed makes the generated data reproducible. Generated files are stored under `data/generated/` and can be recreated when needed.

## Run the Pipeline

See all available command-line options:

```bat
python -m datarecon.pipeline --help
```

Run with a batch ID:

```bat
python -m datarecon.pipeline --batch-id batch_demo_001
```

### Optional customer-reference validation

A customer master file can be supplied to validate customer IDs in both datasets:

```bat
python -m datarecon.pipeline --batch-id reference-check-001 --customers data/sample/customers.csv --output outputs/reference-check --database outputs/reference-check.db
```

The customer file must contain a `customer_id` column with unique, non-empty IDs. Orders referencing unknown customer IDs are quarantined before reconciliation. Missing or unexpected order columns are treated as schema errors.

Use a new batch ID for each new batch. Reusing a batch ID with different data is rejected.

## Outputs

The pipeline produces a machine-readable JSON report and rejected-record CSV files in the configured output directory. These include validation counts, reconciliation results, and execution status.

When using the example customer-reference command, inspect:

- `outputs/reference-check/report.json` — run and reconciliation summary.
- `outputs/reference-check/source_rejects.csv` — rejected source records, if any.
- `outputs/reference-check/target_rejects.csv` — rejected target records, including rejection reasons.

The database stores published records and run history. Exact output filenames and options can be inspected through the pipeline's `--help` output.

## Benchmark Results

The following are three local benchmark runs on Windows, using source and target datasets containing 100,000 rows each.

| Metric | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| Source rows | 100,000 | 100,000 | 100,000 |
| Target rows | 100,000 | 100,000 | 100,000 |
| Runtime (seconds) | 39.6711 | 28.2016 | 26.1939 |
| Source-row throughput (rows/second) | 2,520.73 | 3,545.90 | 3,817.68 |
| Peak traced Python memory (MB) | 37.64 | 37.64 | 37.64 |
| Source-only records | 1 | 1 | 1 |
| Target-only records | 1 | 1 | 1 |
| Field mismatches | 1 | 1 | 1 |

All three runs detected one source-only record, one target-only record, and one field mismatch. The datasets had equal row counts but different contents, so reconciliation returned `matched: false`.

These measurements are observations from local runs, not guaranteed performance. Runtime can vary with machine load and environment. Peak traced Python memory is not the same as total process memory. More repeated runs would provide a stronger performance baseline.

## Limitations and Future Improvements

DataRecon currently runs as a local batch-processing pipeline. Potential improvements include chunked processing for larger files, structured logging, configurable validation rules, more comprehensive recovery across pipeline stages, and repeated benchmarks on representative workloads.

The automated tests cover validation, reconciliation-related pipeline behavior, duplicate handling, publishing idempotency, and publishing rollback/retry. Passing tests does not establish production readiness for every possible failure scenario.

## Repository

GitHub: https://github.com/ErrabelliSathvik/datarecon
