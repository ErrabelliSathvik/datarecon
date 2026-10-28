# AI Assistance and Development Notes

## Why I kept these notes

I used AI assistance at different stages of building DataRecon. It helped me break the challenge into smaller tasks, think through implementation choices, investigate bugs, develop tests, and improve the documentation.

This file records the main areas where I used that assistance. It is a summary of my development process, not a verbatim transcript of every prompt and response.

## 1. Planning the project

I started by breaking the reconciliation problem into smaller parts: reading the input files, validating records, comparing datasets, generating reports, and storing valid records.

AI assistance helped me organize these tasks into separate modules so that I could work on and test each part independently.

## 2. Building the reconciliation logic

I built the reconciliation logic around `order_id`, which is used to match records between the source and target datasets.

The pipeline identifies records that appear in only one dataset and compares field values for matching orders. It also reports row counts and amount totals. I used sample CSV files to check whether the reports reflected the differences in the input data.

## 3. Validating records

I added validation for missing required values, invalid amounts and dates, unsupported statuses, and duplicate order IDs.

Rejected records are kept separately with their original fields, source row numbers, and rejection reasons. During development, I used tests to check the output and identify cases where the implementation did not match the expected results.

## 4. Publishing data and handling repeated batches

I implemented SQLite publishing and added tests for repeated batches, updates to existing orders, duplicate keys, and invalid amounts.

I also added protection against reusing a batch ID with different data. This helps distinguish an identical batch replay from a new batch that happens to use the same ID.

## 5. Testing and debugging

I used AI assistance to explore test cases and investigate failures during development. For example, some publishing tests expected a return field that the implementation did not provide, while another test expected a different format for validation rejection reasons.

I reviewed these mismatches, adjusted the implementation or tests where appropriate, and reran the test suite. The test count and final result should reflect the latest test run performed against the exact code submitted to GitHub.

## 6. Performance testing

I generated synthetic order datasets and ran the benchmark with 100,000 source rows and 100,000 target rows.

Two local runs produced the following results:

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Runtime | 39.6711 seconds | 28.2016 seconds |
| Source-row throughput | 2,520.73 rows/second | 3,545.90 rows/second |
| Peak traced Python memory | 37.64 MB | 37.64 MB |

Both runs reported one source-only record, one target-only record, and one field mismatch. The reconciliation result was `matched: false`, even though both datasets contained the same number of rows.

These measurements were collected locally on Windows. Runtime varied between runs, so the results should be treated as observations rather than guaranteed performance. Peak traced Python memory does not represent total process memory.

## 7. Documentation and GitHub

I used AI assistance to improve the README, architecture notes, data dictionary, and development notes. I also received guidance on Git commands, committing changes, and pushing the repository to GitHub.

Repository: https://github.com/ErrabelliSathvik/datarecon

## 8. Original AI prompts

This document summarizes the main areas where I used AI assistance. It does not contain a complete, verbatim record of the prompts I submitted.

If the challenge requires the original prompts, I will provide the actual prompts or an available conversation export separately. I will not present reconstructed examples as exact historical prompts.

## Review and responsibility

AI suggestions helped me work through parts of the project, but they were not proof that a feature worked correctly. I needed to review the code, run tests, examine the generated results, and consider the limitations of the implementation.

I am responsible for understanding the project's logic, design choices, and limitations so that I can explain them during a review.
