\# Data Dictionary



\## Entity: Orders



\*\*Grain:\*\* One record per `order\_id`.



| Column | Type | Required | Description |

|---|---|---|---|

| `order\_id` | String | Yes | Unique order business key |

| `customer\_id` | String | Yes | Identifier of the customer |

| `order\_date` | ISO date | Yes | Date the order was placed |

| `amount` | Decimal | Yes | Order amount; must be nonnegative |

| `status` | String | Yes | One of pending, completed, shipped, cancelled |



\### Business Rules



\- `order\_id` must be non-null and unique within each input dataset.

\- `customer\_id` must be present.

\- `order\_date` must be parseable as a date.

\- `amount` must be numeric and nonnegative.

\- `status` must belong to the configured set of supported statuses.

\- Source and target records are matched using `order\_id`.

\- Other fields are compared for records with matching keys.



\## Reconciliation Outputs



| Field | Meaning |

|---|---|

| `run\_id` | Unique execution identifier |

| `row\_count\_difference` | Source count minus target count |

| `source\_only\_count` | Number of source keys missing from target |

| `target\_only\_count` | Number of target keys absent from source |

| `field\_mismatch\_count` | Number of differing field comparisons |

| `common\_key\_count` | Number of keys present in both datasets |

| `matched` | Whether keys and compared field values reconcile |



\## Publishing Metadata



The SQLite `target\_orders` table stores order attributes plus `batch\_id` and `source\_file`. The `pipeline\_runs` table stores execution status, timestamps, and validation counts.



\## Assumptions and Limitations



\- Customer IDs are identifiers, but a customer master dataset is not currently validated.

\- Amount aggregates use floating-point values in the current implementation; integer minor units or decimal arithmetic would be preferable for strict financial precision.

\- Full source-row preservation in quarantine is not yet implemented.

\- Historical order changes are overwritten in the target table rather than preserved as versions.



