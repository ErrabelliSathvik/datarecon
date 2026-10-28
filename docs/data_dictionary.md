\# DataRecon Data Dictionary



\## 1. Order input fields



The source and target datasets use the same expected order schema.



| Field | Expected meaning | Validation |

|---|---|---|

| `order\_id` | Unique identifier for an order | Required; duplicate non-empty keys are rejected |

| `customer\_id` | Identifier of the customer associated with the order | Required |

| `order\_date` | Date associated with the order | Required; must be parseable as a date |

| `amount` | Monetary amount for the order | Required; must be numeric and non-negative |

| `status` | Current order status | Required; normalized to lowercase |



\### Allowed statuses



The current validator accepts:



\- `pending`

\- `completed`

\- `shipped`

\- `cancelled`



Values are trimmed and normalized to lowercase before they are used in the valid dataset.



\## 2. Business key



`order\_id` is the business key used to compare source and target records.



The reconciliation logic uses this key to identify records that appear in only one dataset and to compare fields for records that share a key.



Duplicate non-empty order IDs are treated as invalid during validation. The validator rejects every occurrence of a duplicated key rather than choosing one record arbitrarily.



\## 3. Validation and quarantine fields



Rejected records retain their original input fields and include additional diagnostic information.



| Field | Meaning |

|---|---|

| `source\_row\_number` | One-based data-row number from the input, excluding the header |

| `rejection\_reason` | One or more validation reasons associated with the rejected record |



Examples of rejection reasons include:



\- `missing\_required\_field:customer\_id`

\- `invalid\_amount`

\- `negative\_amount`

\- `invalid\_order\_date`

\- `invalid\_status`

\- `duplicate\_order\_id`



A record can have more than one rejection reason. Reasons are joined with semicolons.



\## 4. Reconciliation report



The JSON report summarizes the comparison between the source and target datasets.



| Field | Meaning |

|---|---|

| `source.row\_count` | Number of source records included in reconciliation |

| `source.total\_amount` | Sum of source amounts |

| `target.row\_count` | Number of target records included in reconciliation |

| `target.total\_amount` | Sum of target amounts |

| `reconciliation.row\_count\_difference` | Source row count minus target row count |

| `reconciliation.source\_only\_count` | Number of records found only in the source |

| `reconciliation.target\_only\_count` | Number of records found only in the target |

| `reconciliation.field\_mismatch\_count` | Number of field-level mismatches reported |

| `reconciliation.common\_key\_count` | Number of business keys shared by both datasets |

| `reconciliation.common\_key\_source\_amount` | Source amount total for shared keys |

| `reconciliation.common\_key\_target\_amount` | Target amount total for shared keys |

| `reconciliation.common\_key\_amount\_difference` | Source shared-key amount minus target shared-key amount |

| `reconciliation.matched` | Indicates whether the implemented reconciliation checks found differences |



The exact report structure is defined by `src/datarecon/reconciliation.py`. If the report schema changes, this document should be updated to match it.



\## 5. Discrepancy output files



| File | Purpose |

|---|---|

| `source\_only.csv` | Source records without a matching target business key |

| `target\_only.csv` | Target records without a matching source business key |

| `field\_mismatches.csv` | Field-level differences for shared business keys |

| `source\_rejects.csv` | Invalid source records |

| `target\_rejects.csv` | Invalid target records |



The files are generated in the configured output directory. Their exact columns depend on the corresponding implementation.



\## 6. Publishing and run history



The SQLite database stores published order records and pipeline execution history.



The publishing schema includes fields used to identify orders and track the batch associated with a published record. The batch ledger stores batch identifiers, content hashes, row counts, and publication timestamps.



The run-history table records execution status, timestamps, input and output counts, and error details. See `publishing.py` and `run\_history.py` for the authoritative database schemas.



\## 7. Benchmark metrics



| Metric | Meaning |

|---|---|

| `elapsed\_seconds` | Total elapsed time measured by the benchmark |

| `source\_rows\_per\_second` | Source row count divided by elapsed time |

| `peak\_traced\_python\_memory\_mb` | Peak Python memory recorded by `tracemalloc`, in megabytes |

| `reconciliation\_matched` | Whether the reconciliation result reported a match |



The recorded benchmark is one local run against 100,000 source rows and 100,000 target rows. Results can vary with the environment and input data.



