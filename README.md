# DataRecon — Data Reconciliation Pipeline

## Overview

DataRecon is a Python project that compares two order datasets and helps identify differences between them. It checks for missing records, mismatched field values, and invalid data rather than relying on row counts alone.

The pipeline uses `order_id` to match records in source and target CSV files. It validates the data, generates reconciliation reports, and publishes valid source records to a SQLite database.

## Features

- Match source and target orders using `order_id`.
- Find records that appear in only one dataset.
- Detect field-level differences between matching orders.
- Validate required fields, amounts, dates, statuses, and duplicate order IDs.
- Separate invalid records and record rejection reasons.
- Publish validated orders to SQLite.
- Prevent a batch ID from being reused with different data.
- Keep a history of pipeline executions.
- Generate repeatable synthetic datasets for testing.
- Run automated tests and performance benchmarks.

## Technologies Used

- Python
- pandas
- NumPy
- SQLite
- pytest

## Setup

Create a virtual environment and activate it on Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
```

Install the project dependencies:

```bat
python -m pip install -r requirements.txt
```

Set the source directory so Python can find the project modules:

```bat
set PYTHONPATH=src
```

Run these commands from the project root directory.

## Run the Tests

Use pytest to run the test suite:

```bat
python -m pytest -v
```

## Generate Test Data

To generate source and target datasets with 100,000 rows using a fixed random seed, run:

```bat
python scripts\generate_data.py --rows 100000 --seed 42
```

Using the same seed makes the generated data reproducible.

## Run the Pipeline

To see the available command-line options:

```bat
python -m datarecon.pipeline --help
```

To run the pipeline with a batch ID:

```bat
python -m datarecon.pipeline --batch-id batch_demo_001
```

Use a new batch ID for each new batch. If you rerun a batch, make sure its data is unchanged.

## Benchmark Results

I ran a local benchmark using source and target CSV files containing 100,000 rows each.

| Metric | Result |
|---|---:|
| Source rows | 100,000 |
| Target rows | 100,000 |
| Runtime | 25.42 seconds |
| Source-row throughput | 3,933.53 rows/second |
| Peak traced Python memory | 37.64 MB |
| Source-only records | 1 |
| Target-only records | 1 |
| Field mismatches | 1 |

The pipeline detected one source-only record, one target-only record, and one field mismatch. The datasets had the same number of rows, but their contents were different, so the reconciliation report correctly returned `matched: false`.

These results are from a single run on my Windows machine. Performance may vary depending on the hardware, input data, and environment. The memory figure represents traced Python memory, not total process memory.

## Design Choices

I used pandas to load and compare tabular data, SQLite to store published records and pipeline history, and `order_id` as the key for matching orders. Synthetic data generation uses a fixed random seed so that test datasets can be reproduced.

## Limitations and Future Improvements

DataRecon currently runs as a local batch-processing pipeline. Some areas that could be improved include processing larger files in chunks, adding structured logging, making validation rules configurable, and running repeated benchmarks to get a more reliable view of performance.

## Repository

GitHub: https://github.com/ErrabelliSathvik/datarecon
