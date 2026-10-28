# DataRecon System Architecture

## Overview

DataRecon is a Python project that compares source and target order datasets to find missing records, mismatched values, and invalid data. It uses CSV files as input, pandas for data processing, and SQLite to store published orders and pipeline run history.

I separated the main tasks into different modules so that validation, reconciliation, and publishing can be tested independently.

## How the Architecture Works

```text
Source CSV                  Target CSV
    |                            |
    v                            v
Source Validation          Target Validation
    |                            |
    v                            v
Source Rejects              Target Rejects
    |                            |
    +-------------+--------------+
                  |
                  v
          Reconciliation
                  |
         +--------+--------+
         |        |        |
         v        v        v
     Source-only Target-only Field mismatches
                  |
                  v
        JSON Report and CSV Files


Validated Source Records
           |
           v
     SQLite Publishing
           |
           v
      Published Orders


Pipeline Execution
           |
           v
        Run History
```

## Main Components

### Validation

The validation module checks required fields, amounts, dates, order statuses, and duplicate order IDs. Records that fail validation are separated from valid records, with their original data and rejection reasons preserved for review.

### Reconciliation

The reconciliation module uses `order_id` to match records between the two datasets. It identifies records found in only one dataset and compares field values for matching orders. It also reports row counts and amount totals.

### Database Publishing

The publishing module writes validated source records to SQLite. Existing orders can be updated when a later batch contains new values. Batch replay protection also checks whether a batch ID has already been used with different data.

### Run History

The run-history module stores information about pipeline executions, including their status, timestamps, row counts, and errors. This makes it easier to review previous runs.

### Synthetic Data Generation

A separate script generates test datasets using a fixed random seed. This makes it possible to reproduce test data and run benchmarks with consistent inputs.

## Pipeline Flow

1. Load the source and target CSV files.
2. Validate the records in both datasets.
3. Save invalid records to separate quarantine files.
4. Compare the validated datasets using the business key.
5. Generate a JSON report and CSV files containing the differences.
6. Publish valid source records to SQLite.
7. Save the execution result in the run-history database.

## Reliability

The project includes checks for invalid data and duplicate business keys. Rejected records retain information about why they failed validation. The publishing logic also includes batch replay protection, and automated tests cover several normal and invalid input scenarios.

The fixed random seed helps reproduce the synthetic datasets used during testing.

## Design Choices

I used CSV because the input and output files are easy to inspect without additional infrastructure. Pandas makes it convenient to compare tabular data, while SQLite provides persistent storage without requiring a separate database server.

This setup works well for a local prototype. However, pandas can consume more memory as datasets grow, and SQLite may not be the best choice for a distributed system with many concurrent writers.

## Limitations and Future Improvements

The current implementation focuses on local batch processing. Some areas that could be improved include structured logging, configurable validation rules, schema versioning, better recovery from partial failures, and chunked processing for larger datasets.

The benchmark results should be interpreted in the context of the machine and dataset used for testing. Repeated runs would provide a more reliable view of performance.
