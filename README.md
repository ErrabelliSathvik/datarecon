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



\## Performance



Benchmark results should be added after running the benchmark script. Report the actual row count, runtime, throughput, memory measurement, and test results.



\## Submission Checklist



\- \[ ] Source code and tests included.

\- \[ ] Dependencies listed in `requirements.txt`.

\- \[ ] Sample datasets included.

\- \[ ] Installation and execution commands verified.

\- \[ ] Architecture and trade-offs documented.

\- \[ ] AI prompt history included as required.

\- \[ ] Public GitHub repository verified.

\- \[ ] No secrets or API keys committed.



