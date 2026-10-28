\# DataRecon — System Architecture



\## 1. Overview



DataRecon is a local data reconciliation pipeline that validates source and target order datasets, identifies discrepancies, quarantines invalid records, and publishes valid source records to a SQLite database.



\## 2. Architecture



```text

Source CSV                 Target CSV

&#x20;   |                           |

&#x20;   v                           v

Source Validation         Target Validation

&#x20;   |                           |

&#x20;   v                           v

Source Rejects            Target Rejects

&#x20;   |                           |

&#x20;   +-------------+-------------+

&#x20;                 |

&#x20;                 v

&#x20;         Reconciliation Engine

&#x20;                 |

&#x20;       +---------+---------+

&#x20;       |         |         |

&#x20;       v         v         v

&#x20;   Source-only Target-only Field mismatches

&#x20;                 |

&#x20;                 v

&#x20;         JSON Report + CSVs



Validated Source Records

&#x20;          |

&#x20;          v

&#x20;   SQLite Publishing

&#x20;          |

&#x20;          v

&#x20;   Published Orders



Pipeline Execution

&#x20;          |

&#x20;          v

&#x20;     Run History

```



\## 3. Main Components



\### Validation



Checks required fields, numeric amounts, order dates, permitted statuses, and duplicate business keys. Invalid records are quarantined with source row numbers and rejection reasons.



\### Reconciliation



Uses `order\_id` as the business key. Identifies records that exist only in one dataset and field-level differences between records with matching keys. Also reports row counts and aggregate amounts.



\### Publishing



Publishes validated source records into SQLite. Business-key upserts allow existing orders to be updated. Batch replay protection prevents a previously used batch ID from being reused with different content.



\### Run History



Stores pipeline execution status, timestamps, row counts, and error details in SQLite.



\### Synthetic Data Generation



Creates reproducible order datasets using a fixed random seed. Generated datasets can be used for correctness tests and performance benchmarks.



\## 4. Data Flow



1\. Read the source and target CSV files.

2\. Validate both datasets.

3\. Save invalid records to quarantine outputs.

4\. Reconcile the valid datasets.

5\. Produce the JSON report and discrepancy CSV files.

6\. Publish validated source records to SQLite.

7\. Record the execution result in run history.



\## 5. Reliability Considerations



\- Required-field and domain validation.

\- Duplicate business-key detection.

\- Quarantine with rejection reasons.

\- Database transactions.

\- Idempotent batch replay handling.

\- Automated tests for normal and invalid inputs.

\- Reproducible synthetic datasets.



\## 6. Design Trade-offs



\- \*\*CSV:\*\* Simple and portable, but not ideal for concurrent high-volume ingestion.

\- \*\*Pandas:\*\* Convenient for tabular comparison, but can consume substantial memory for large datasets.

\- \*\*SQLite:\*\* Easy to run locally without a database server, but less suitable for distributed concurrent workloads.

\- \*\*Batch processing:\*\* Supports repeatable runs, though large datasets may eventually require chunked processing.



\## 7. Known Limitations



This implementation is a local prototype. Production hardening could include structured logging, schema versioning, configurable business rules, stronger recovery workflows, and chunked processing.



Performance claims must be based on measured benchmark results.



