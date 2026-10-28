\# DataRecon — Data Reconciliation Pipeline



\## Overview



DataRecon is a Python project for comparing two order datasets and finding differences between them. It checks more than row counts: it identifies missing records, field mismatches, and invalid data.



The project uses `order\_id` to match records between source and target CSV files. It validates records, produces reconciliation reports, and publishes valid source records to SQLite.



\## Features



\- Compare source and target records using `order\_id`.

\- Identify records present in only one dataset.

\- Detect field-level differences for matching orders.

\- Validate required fields, amounts, dates, statuses, and duplicate order IDs.

\- Quarantine invalid records with rejection reasons.

\- Publish validated orders to SQLite.

\- Protect against reusing a batch ID with different data.

\- Store pipeline execution history.

\- Generate reproducible synthetic datasets.

\- Run automated tests and performance benchmarks.



\## Technologies



\- Python

\- pandas

\- NumPy

\- SQLite

\- pytest



\## Setup



Create and activate a virtual environment:



```bat

python -m venv .venv

.venv\\Scripts\\activate

```



Install dependencies:



```bat

python -m pip install -r requirements.txt

```



Configure the source directory:



```bat

set PYTHONPATH=src

```



\## Run Tests



```bat

python -m pytest -v

```



\## Generate Test Data



```bat

python scripts\\generate\_data.py --rows 100000 --seed 42

```



\## Run the Pipeline



Check the available command-line options:



```bat

python -m datarecon.pipeline --help

```



Run the sample pipeline using a unique batch ID:



```bat

python -m datarecon.pipeline --batch-id batch\_demo\_001

```



\## Benchmark Results



In one local benchmark run, I processed source and target CSV files containing 100,000 rows each.



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



The reconciliation detected all three discrepancies. Although the two datasets had equal row counts, their contents differed, so the report correctly returned `matched: false`.



These figures come from one run on my local Windows environment. Runtime and memory usage may vary on other systems.



\## Design Choices



I used pandas to work with CSV data, SQLite for local persistent storage, and `order\_id` as the business key. A fixed random seed makes generated datasets reproducible.



\## Limitations and Future Improvements



This version is a local batch-processing prototype. Possible improvements include chunked processing for larger datasets, structured logging, configurable validation rules, and repeated benchmarks to compare performance across runs.



\## Repository



GitHub: https://github.com/ErrabelliSathvik/datarecon



