\# DataRecon Architecture



\## Overview



DataRecon compares two order datasets and reports where they differ. The current implementation is a local Python application that uses CSV files for input, pandas for data processing, and SQLite for persistent storage.



I separated validation, reconciliation, publishing, and run-history tracking into different modules so that each part can be tested independently.



\## How the pipeline works



1\. Read the source and target CSV files.

2\. Validate both datasets against the expected order fields.

3\. Separate invalid records and preserve their rejection reasons.

4\. Compare the validated datasets using `order\_id`.

5\. Write a JSON reconciliation report and CSV files containing discrepancies.

6\. Publish valid source records to SQLite.

7\. Record the pipeline outcome in the run-history database.



The exact execution order and error-handling behavior should be checked against `src/datarecon/pipeline.py`.



\## Main components



\### `validation.py`



Checks the required fields, amounts, dates, statuses, and duplicate order IDs. Valid records are normalized before publishing. Invalid records are returned separately with source-row information and rejection reasons.



\### `reconciliation.py`



Compares source and target records using `order\_id` as the business key. It identifies records found only in the source, records found only in the target, and field-level differences for shared keys.



It also reports row counts and amount aggregates. Matching row counts alone do not mean the datasets are equivalent.



\### `publishing.py`



Writes validated source records to SQLite. The publishing logic uses `order\_id` to identify existing orders and supports updating them with a later batch.



It also records published batch IDs and content hashes to distinguish an identical replay from reuse of the same batch ID with different data.



\### `run\_history.py`



Stores execution information in SQLite, including run status, timestamps, counts, and error information.



\### Supporting scripts



\- `generate\_data.py` creates reproducible synthetic order datasets.

\- `benchmark.py` measures reconciliation runtime and records performance metrics.

\- `show\_runs.py` displays saved run-history records.



\## Data flow



```text

Source CSV ------------------+

&#x20;                            |

&#x20;                            v

&#x20;                      Validation

&#x20;                            |

&#x20;                 +----------+----------+

&#x20;                 |                     |

&#x20;            Valid records          Rejected records

&#x20;                 |                     |

&#x20;                 v                     v

&#x20;            Reconciliation        Quarantine CSVs

&#x20;                 |

&#x20;                 v

&#x20;       JSON report and discrepancy CSVs



Validated source records

&#x20;         |

&#x20;         v

&#x20;    SQLite publishing

&#x20;         |

&#x20;         v

&#x20;     Published orders



Pipeline execution

&#x20;         |

&#x20;         v

&#x20;      Run history

```



\## Technology choices



\*\*Python and pandas:\*\* These provide convenient CSV loading, tabular validation, and comparison operations.



\*\*CSV:\*\* Input and output files are easy to inspect and share without requiring an external service.



\*\*SQLite:\*\* It provides persistent storage without requiring a separate database server. It suits this local prototype, although a larger multi-user deployment might need a different database.



\*\*pytest:\*\* Automated tests cover reconciliation, validation, edge cases, and publishing behavior.



\## Reliability considerations



The project includes duplicate-key validation, invalid-record quarantine, batch replay protection, and automated tests. These mechanisms help detect data-quality problems and reduce the risk of accidental duplicate processing.



They do not replace a full production recovery strategy. Database transactions, error handling, and the behavior of partial pipeline failures should be reviewed in the implementation.



\## Benchmark observations



In one local run, the reconciliation processed 100,000 source rows and 100,000 target rows in 25.4225 seconds. The benchmark reported 3,933.53 source rows per second and 37.64 MB of peak traced Python memory.



The run detected one source-only record, one target-only record, and one field mismatch.



These measurements are specific to that run and environment. Traced Python memory does not represent the entire process's memory usage.



\## Limitations and possible improvements



The current application is designed for local batch processing. Pandas may consume more memory as datasets grow, and CSV parsing errors may need handling before record-level validation begins.



Possible improvements include chunked processing, structured logging, configurable schemas and business rules, stronger recovery handling, and repeated benchmark runs.



