\# DataRecon — Data Reconciliation Pipeline



A Python-based data reconciliation project that compares source and target order datasets, validates records, identifies discrepancies, quarantines invalid data, and publishes clean records to SQLite.



\## Features



\- Reconciliation of source and target datasets using business keys.

\- Row-count and aggregate comparisons.

\- Field-level mismatch detection.

\- Validation of required fields, dates, amounts, and statuses.

\- Quarantine of invalid records with rejection reasons.

\- SQLite publishing with batch replay protection.

\- Pipeline run-history tracking.

\- Reproducible synthetic data generation.

\- Automated tests and performance benchmarking.



\## Project Structure



```text

datarecon/

├── src/datarecon/

├── tests/

├── scripts/

├── data/sample/

├── data/generated/

├── outputs/

├── docs/

├── requirements.txt

└── README.md

```



\## Requirements



\- Python

\- pip

\- Dependencies listed in `requirements.txt`



\## Installation



Create and activate a virtual environment:



```bat

python -m venv .venv

.venv\\Scripts\\activate

```



Install dependencies:



```bat

python -m pip install -r requirements.txt

```



Configure Python imports:



```bat

set PYTHONPATH=src

```



\## Run Tests



```bat

python -m pytest -v

```



\## Generate Synthetic Data



```bat

python scripts/generate\_data.py --rows 100000 --seed 42

```



\## Run the Pipeline



```bat

python -m datarecon.pipeline --batch-id batch\_demo\_001

```



Check the pipeline's available options with:



```bat

python -m datarecon.pipeline --help

```



\## Reconciliation Outputs



Depending on the configured output directory, the pipeline may produce:



\- `reconciliation\_report.json`

\- `source\_only.csv`

\- `target\_only.csv`

\- `field\_mismatches.csv`

\- `source\_rejects.csv`

\- `target\_rejects.csv`



SQLite stores published orders and pipeline run history.



\## Validation and Reliability



The pipeline validates required fields, amounts, dates, statuses, and duplicate business keys. Invalid records are quarantined with source row numbers and rejection reasons.



Batch replay protection prevents an existing batch ID from being reused with different content.



\## Design Decisions



\- \*\*Pandas:\*\* Tabular processing and data validation.

\- \*\*SQLite:\*\* Persistent storage for published orders and run history.

\- \*\*CSV:\*\* Portable input datasets and inspectable outputs.

\- \*\*Fixed random seed:\*\* Reproducible synthetic test data.

\- \*\*Business keys:\*\* Identification of missing records and field-level differences.



\## Limitations



This is a local CSV-to-SQLite prototype. Performance depends on dataset size and hardware. Production use would benefit from structured logging, monitoring, schema versioning, and additional recovery mechanisms.



\## Performance Benchmark



\### Test Configuration



\- \*\*Source dataset:\*\* 100,000 rows

\- \*\*Target dataset:\*\* 100,000 rows

\- \*\*Random seed:\*\* 42

\- \*\*Environment:\*\* Windows, Python 3.15.1

\- \*\*Benchmark duration:\*\* 25.4225 seconds



\### Measured Results



| Metric | Result |

|---|---:|

| Source rows | 100,000 |

| Target rows | 100,000 |

| Elapsed time | 25.42 seconds |

| Source-row throughput | 3,933.53 rows/second |

| Peak traced Python memory | 37.64 MB |

| Source-only records | 1 |

| Target-only records | 1 |

| Field mismatches | 1 |

| Common business keys | 99,999 |



\### Correctness



The benchmark detected one source-only record, one target-only record, and one field-level mismatch. The reconciliation correctly reported `matched: false`.



The source and target contain the same number of rows, but equal row counts do not imply equivalent datasets.



\### Limitations



These measurements represent a single benchmark run and may vary with hardware, system load, and dataset characteristics. Traced Python memory is not the same as total process memory. Further repeated runs would be needed for a more robust performance evaluation.



