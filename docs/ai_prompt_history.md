# AI Assistance and Development Notes

## Why I kept these notes

I used AI assistance at different stages of building DataRecon. It helped me break the problem into smaller tasks, work through bugs, write tests, and make the documentation easier to follow.

This document describes how I used that help during development. It is a summary of the main activities, not a word-for-word record of every conversation.

## 1. Planning the project

I began by dividing the reconciliation process into smaller parts: reading the input files, checking the data, comparing the source and target datasets, generating reports, and storing valid records.

AI assistance helped me think through how to organize these responsibilities into separate modules. This made it easier to work on each part and test it independently.

## 2. Building the reconciliation logic

I built the reconciliation logic around `order_id`, which is used to match records between the source and target datasets.

The pipeline identifies records that appear in only one dataset and compares field values for matching orders. It also reports row counts and amount totals. I used sample CSV files to check whether the reports correctly reflected the differences in the input data.

## 3. Validating records

I added validation for missing required values, invalid amounts and dates, unsupported statuses, and duplicate order IDs.

Rejected records are kept separately with their original fields, source row numbers, and rejection reasons. While developing this part, I used tests to check the output and identify cases where the implementation and expected results did not agree.

## 4. Publishing data and handling repeated batches

I implemented SQLite publishing and added tests for repeated batches, updates to existing orders, duplicate keys, and invalid amounts.

I also added a check to prevent the same batch ID from being reused with different data. The intention is to avoid treating changed input as if it were an unchanged rerun of the original batch.

## 5. Testing and debugging

I used AI assistance to explore test cases and investigate failures during development. For example, some tests expected a return field that the implementation did not provide, while another expected a different format for validation rejection reasons.

I reviewed these mismatches, adjusted the code or tests where needed, and reran the test suite. An earlier run completed with 10 passing tests. The final test result should be confirmed against the version submitted to GitHub.

## 6. Performance testing

I generated synthetic order datasets and ran the benchmark with 100,000 source rows and 100,000 target rows.

Two recent runs produced the following results:

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Runtime | 39.6711 seconds | 28.2016 seconds |
| Source-row throughput | 2,520.73 rows/second | 3,545.90 rows/second |
| Peak traced Python memory | 37.64 MB | 37.64 MB |

Both runs reported one source-only record, one target-only record, and one field mismatch. The reconciliation result was `matched: false`, even though both datasets contained the same number of rows.

These measurements were taken locally on Windows. The runtime varied between runs, so they should be treated as observations rather than guaranteed performance. Peak traced Python memory is not the same as total process memory.

## 7. Documentation and GitHub

I used AI assistance to improve the README, architecture notes, data dictionary, and development notes. I also followed guidance for using Git, committing changes, and pushing the project to GitHub.

Repository: https://github.com/ErrabelliSathvik/datarecon

## Review and responsibility

AI suggestions were useful during development, but I still needed to check whether the proposed solutions worked with my code. I used tests and sample data to investigate issues and verify the results.

I am responsible for understanding the implementation, its design choices, and its limitations so I can explain them during a review.

This document summarizes the main ways I used AI assistance. If the challenge requires the original prompts or conversation history, I will provide those separately rather than presenting this summary as a verbatim transcript.