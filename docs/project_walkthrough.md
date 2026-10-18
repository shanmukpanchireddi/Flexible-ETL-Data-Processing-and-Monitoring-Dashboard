# Project Walkthrough

## Purpose

This document explains how the Project 1 DB-backed ETL pipeline works from source CSV input through to SQLite verification.

The goal is to make the project explainable to a reviewer, hiring manager, or interviewer without needing to inspect every line of code first.

---

## Project 1 overview

Project 1 is a local DB-backed batch ETL pipeline.

It takes transaction CSV data, validates it, separates clean and rejected rows, loads both outputs into SQLite, and verifies the result with SQL.

The project is intentionally small. The value is in the engineering behaviour:

- schema validation
- row-level validation
- reject handling
- traceability
- rerun safety
- SQL verification
- tests and CI

---

## End-to-end flow

```text
raw.csv
  ↓
etl.py
  ↓
clean.csv + rejected.csv
  ↓
sqlite_load.py
  ↓
clean_transactions + rejected_transactions
  ↓
queries.sql
```

---

## 1. Source input

The pipeline starts from a CSV file such as:

```text
raw.csv
```

The expected source columns are transaction fields such as:

- `transaction_id`
- `amount`
- `currency`

The exact input contract is enforced by `etl.py`.

---

## 2. Schema validation

Before processing rows, the ETL checks that required headers exist.

If required headers are missing, the pipeline fails loud with a clear error instead of silently producing bad outputs.

This is intentional.

A schema problem means the file shape is wrong, so continuing the run would make later results untrustworthy.

Example bad-schema test file:

```text
raw_bad.csv
```

Expected behaviour:

- the run fails
- an error is logged
- a `ValueError` explains which required headers are missing

---

## 3. Row validation

After schema validation passes, each row is checked.

Typical validation rules include:

- transaction ID must exist
- amount must be valid and positive
- currency must be valid
- duplicate transaction IDs within a run should be rejected

Rows that pass validation are treated as clean.

Rows that fail validation are treated as rejects.

---

## 4. Clean and rejected outputs

The ETL writes two local output files:

```text
clean.csv
rejected.csv
```

### `clean.csv`

Contains accepted rows.

Expected columns:

```text
transaction_id,amount,currency,run_id
```

### `rejected.csv`

Contains rejected rows.

Expected columns:

```text
transaction_id,amount,currency,error_reason,run_id
```

The `error_reason` field is important because it makes data quality failures inspectable instead of invisible.

---

## 5. Run traceability

Each processed row receives a `run_id`.

The `run_id` allows rows to be traced back to a specific pipeline execution.

This supports questions such as:

- how many rows were accepted in this run?
- how many rows were rejected in this run?
- what reject reasons occurred in this run?
- did a rerun duplicate records?

---

## 6. SQLite loading

`sqlite_load.py` loads the generated clean and rejected outputs into SQLite.

It creates and loads:

- `clean_transactions`
- `rejected_transactions`

The local SQLite database is:

```text
etl.db
```

This file is generated locally and ignored by Git.

---

## 7. Idempotency

The SQLite load is designed to be rerun-safe.

The project uses uniqueness constraints and `INSERT OR IGNORE`.

This means rerunning the loader should not keep inserting duplicate copies of the same records.

Idempotency matters because real pipelines are often replayed after failures, fixes, or backfills.

A rerun-safe load should not inflate the data just because the same job was executed again.

---

## 8. SQL verification

`queries.sql` is the Project 1 verification query pack.

It is used to inspect whether the pipeline behaved correctly after loading data into SQLite.

Useful checks include:

- clean row counts
- rejected row counts
- totals by currency
- reject reasons by run
- duplicate checks
- clean vs rejected counts

This is important because a data pipeline is not complete just because code runs. It must also prove the output is correct.

---

## 9. Tests and CI

The repo includes tests and GitHub Actions CI.

The tests support confidence that key pipeline behaviours keep working as the project changes.

This is part of making the repo maintainable rather than just a one-off script.

---

## 10. Current extension: analytical model layer

Project 1 established the DB-backed ETL pipeline:

- raw CSV input
- clean/rejected output split
- SQLite loading
- idempotent inserts
- SQL verification queries
- tests and CI

The repo has now started the Project 2 analytical model layer.

Current Project 2 files:

- `model_schema.sql` defines the first analytical model tables
- `model_load.sql` loads model tables from Project 1 SQLite outputs
- `analytics_queries.sql` contains OLAP-style queries over the model

The current model introduces:

- `fact_transactions`
- `dim_currency`
- `dim_run`

`dim_date` is intentionally deferred until transaction date exists as a reliable source field.

---

## 11. What this project demonstrates

This project demonstrates:

- local batch ETL design
- validation before transformation
- fail-loud schema handling
- row-level reject classification
- clean/rejected output separation
- run-level traceability
- SQLite loading
- rerun-safe insert behaviour
- SQL verification
- early analytical model progression

---

## 12. Interview explanation

A concise explanation of the project:

> This is a small batch ETL pipeline that reads transaction CSV data, validates the schema and rows, separates clean and rejected records, loads both into SQLite, and verifies the result with SQL. The project focuses on correctness, rerun safety, and explainability rather than scale. It also starts a simple analytical model layer so the cleaned transaction data can be queried through fact and dimension tables.
