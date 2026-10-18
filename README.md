# etl-mini-pipeline

A small batch data engineering project that reads transaction CSV data, validates and classifies rows, writes clean/rejected outputs, loads those outputs into SQLite, and builds the first slice of a simple analytical model layer.

The goal of this project is not just to transform data. The goal is to make pipeline behaviour visible, explainable, testable, and rerun-safe.

---

## Current state

This repo currently covers two connected stages:

1. **Project 1 — DB-backed ETL pipeline**
   - CSV input
   - schema validation
   - row validation
   - clean/rejected output split
   - SQLite loading
   - idempotent inserts
   - SQL verification
   - tests and CI

2. **Project 2 — analytical model layer started**
   - simple fact/dimension model
   - `fact_transactions`
   - `dim_currency`
   - `dim_run`
   - OLAP-style analytical queries
   - model verification checks

The project is intentionally small and local-first. It is designed to demonstrate data engineering fundamentals clearly before adding cloud, orchestration, or distributed processing.

---

## What this project does

The pipeline processes transaction-style CSV data and:

- validates the expected schema
- parses and validates each row
- separates accepted rows from rejected rows
- attaches `run_id` for traceability
- writes clean and rejected output files
- loads clean and rejected rows into SQLite
- prevents duplicate inserts on rerun
- verifies pipeline state with SQL queries
- starts an analytical model from the cleaned transaction table
- verifies that the model preserves expected source counts and grain

---

## Why this project exists

This project demonstrates core junior data engineering skills in a small, explainable system:

- schema validation
- data quality classification
- clean vs rejected output handling
- explicit `error_reason` values
- run-level traceability
- idempotent database loading
- SQL-based verification
- basic analytical modelling
- model verification against source tables
- testable Python functions
- CI-backed repo hygiene

It is intended to show real engineering evidence, not just code that runs once.

---

## Pipeline flow

High-level flow:

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
  ↓
model_schema.sql + model_load.sql
  ↓
fact_transactions + dim_currency + dim_run
  ↓
analytics_queries.sql
  ↓
model_verification.sql
```

---

## Project structure

```text
etl-mini-pipeline/
├── .github/workflows/        # GitHub Actions CI
├── docs/                     # Project walkthrough and model design notes
├── tests/                    # Unit tests
├── etl.py                    # CSV ETL: validation, clean/reject outputs, run_id
├── sqlite_load.py            # SQLite clean/rejected table creation and loading
├── queries.sql               # Project 1 verification query pack
├── model_schema.sql          # Project 2 analytical model schema
├── model_load.sql            # Loads analytical model from clean transaction data
├── analytics_queries.sql     # OLAP-style queries over the analytical model
├── model_verification.sql    # Project 2 model verification checks
├── raw.csv                   # Sample input data
├── raw_bad.csv               # Bad-schema input for failure testing
├── .gitignore
└── README.md
```

---

## Key files

### `etl.py`

Main ETL script.

Responsibilities:

- read transaction CSV input
- validate required headers
- parse and validate rows
- classify bad rows into rejects
- deduplicate repeated transaction IDs within a run
- attach `run_id`
- write clean and rejected output CSV files

### `sqlite_load.py`

SQLite loading script.

Responsibilities:

- create `clean_transactions`
- create `rejected_transactions`
- load `clean.csv`
- load `rejected.csv`
- use uniqueness constraints and `INSERT OR IGNORE` to make reruns safe

### `queries.sql`

Project 1 verification query pack.

Used to check:

- clean table row counts
- rejected table row counts
- totals by currency
- duplicate rows
- reject reasons by run
- clean vs rejected counts

### `model_schema.sql`

Creates the first analytical model tables:

- `fact_transactions`
- `dim_currency`
- `dim_run`

### `model_load.sql`

Loads the analytical model tables from Project 1 SQLite data.

### `analytics_queries.sql`

Runs OLAP-style analytical queries over the model, including:

- total amount by currency
- transaction count by currency
- total amount by pipeline run

### `model_verification.sql`

Project 2 model verification query pack.

Used to check:

- fact table row counts against the cleaned source table
- dimension counts against distinct source values
- rerun safety for model loading
- whether the analytical model preserves the expected transaction grain

---

## SQLite tables

### Project 1 tables

#### `clean_transactions`

Stores accepted transaction rows.

Expected columns:

- `transaction_id`
- `amount`
- `currency`
- `run_id`

Purpose:

- store validated transaction data
- support SQL verification
- provide the source for the analytical model layer

#### `rejected_transactions`

Stores rejected transaction rows.

Expected columns:

- `transaction_id`
- `amount`
- `currency`
- `error_reason`
- `run_id`

Purpose:

- preserve rejected source rows
- make data quality failures inspectable
- support reject-count and reject-reason analysis

---

### Project 2 analytical model tables

#### `fact_transactions`

One row represents one accepted transaction.

Current grain:

```text
one row = one accepted transaction
```

Measures:

- `amount`

References:

- `currency_key`
- `run_key`

#### `dim_currency`

Describes the transaction currency.

#### `dim_run`

Describes the pipeline run that produced the transaction.

---

## Rerun safety / idempotency

The SQLite load is designed to be rerun-safe.

The project uses:

- explicit uniqueness constraints
- `INSERT OR IGNORE`

This means replaying the same load should not inflate row counts with duplicate records.

The intended behaviour is:

- rerunning the ETL can regenerate local output files
- rerunning the SQLite loader should not duplicate already-loaded rows
- rerunning the model load should not duplicate model rows
- verification queries should prove whether duplicates exist

---

## How to run

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Run tests

```bash
pytest
```

### 3. Run the ETL

```bash
python etl.py --input raw.csv --clean clean.csv --reject rejected.csv
```

This creates local generated outputs:

- `clean.csv`
- `rejected.csv`

These files are ignored by Git.

### 4. Run the schema failure example

```bash
python etl.py --input raw_bad.csv
```

Expected behaviour:

- the pipeline fails loud
- an error is logged
- a `ValueError` identifies the missing required headers

### 5. Load outputs into SQLite

```bash
python sqlite_load.py
```

This creates a local SQLite database:

```text
etl.db
```

The database file is ignored by Git.

### 6. Run Project 1 verification queries

```bash
sqlite3 etl.db < queries.sql
```

### 7. Create analytical model tables

```bash
sqlite3 etl.db < model_schema.sql
```

### 8. Load the analytical model

```bash
sqlite3 etl.db < model_load.sql
```

### 9. Run analytical queries

```bash
sqlite3 etl.db < analytics_queries.sql
```

### 10. Run Project 2 model verification checks

```bash
sqlite3 etl.db < model_verification.sql
```

---

## Clean local reset

To remove local generated artifacts:

```bash
rm -f clean.csv rejected.csv etl.db
```

Then rerun the project from the ETL step.

---

## Output files

### `clean.csv`

Expected columns:

```text
transaction_id,amount,currency,run_id
```

### `rejected.csv`

Expected columns:

```text
transaction_id,amount,currency,error_reason,run_id
```

---

## Failure modes

| Failure type | Behaviour |
|---|---|
| Missing required header | Pipeline fails loud with `ValueError` |
| Blank transaction ID | Row is rejected |
| Invalid amount | Row is rejected |
| Invalid currency | Row is rejected |
| Duplicate transaction ID within a run | Row is rejected |
| Replayed DB load | Duplicate inserts are ignored |
| Replayed model load | Duplicate model inserts should be prevented or detected by verification checks |

---

## Verification questions

After running the project, the repo should help answer:

- Did schema validation pass?
- How many rows were cleaned?
- How many rows were rejected?
- Why were rows rejected?
- Were duplicate clean rows prevented?
- Were duplicate rejected rows prevented?
- What is the total amount by currency?
- How many transactions exist by currency?
- What is the total accepted amount by pipeline run?
- How does the analytical model relate to the cleaned transaction table?
- Do the model verification checks prove that fact and dimension counts match the source data?

---

## Additional documentation

More detailed project notes are available in the `docs/` folder:

- [`docs/project_walkthrough.md`](docs/project_walkthrough.md) explains the Project 1 DB-backed ETL pipeline, including validation, clean/rejected outputs, SQLite loading, idempotency, and verification.
- [`docs/model_design.md`](docs/model_design.md) explains the current Project 2 analytical model direction, including grain, fact/dimension choices, and intended OLAP-style queries.

---

## Current milestone

Current state:

- Project 1 DB-backed ETL pipeline is established.
- Clean and rejected rows are loaded into SQLite.
- SQL verification queries exist.
- Tests and CI are present.
- Project 2 analytical modelling has started with a small fact/dimension model.
- Project 2 model verification checks are present.

Current Project 2 model:

- `fact_transactions`
- `dim_currency`
- `dim_run`

`dim_date` is intentionally deferred until the source pipeline includes a reliable date field.

---

## What this project demonstrates

This repo currently demonstrates:

- Python ETL scripting
- schema validation
- row-level validation
- error classification
- clean/rejected output handling
- run-level traceability
- SQLite loading
- idempotent insert strategy
- SQL verification
- basic dimensional modelling
- model verification
- GitHub Actions CI
- documentation linked to implementation

---

## Constraints / current boundaries

This project is intentionally small and focused.

It does not currently aim to be:

- a distributed pipeline
- a cloud-native pipeline
- a streaming system
- a production orchestration system
- a full warehouse

The current focus is correctness, explainability, local execution, and portfolio-quality fundamentals.

---

## Next improvements

Potential next improvements:

- add loader-focused integration tests
- strengthen reconciliation between source, clean, rejected, database, and model counts
- expand analytical queries to at least 5 OLAP-style questions
- add a reliable transaction date field before introducing `dim_date`
- tighten docs as Project 2 develops

---

## Summary

`etl-mini-pipeline` is a small but deliberate data engineering repo built to show:

- reliable CSV ETL
- clean vs rejected output handling
- rerun-safe SQLite loading
- SQL verification
- early analytical modelling
- model verification checks
- practical, explainable data engineering fundamentals

## Run the visual dashboard

Open a terminal in this project folder and run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (usually http://localhost:8501). Upload a CSV or use raw.csv, run the pipeline, inspect accepted/rejected records, download the output CSVs, and view SQLite counts. This runs locally and does not publish the app to the internet.

## Flexible CSV dashboard

The Streamlit dashboard supports two modes:

- **Generic CSV mode** accepts different CSV headers and lets you choose columns that must be non-empty, columns that must be numeric, and an optional column for duplicate detection. It creates downloadable clean/rejected CSV files and stores generic records as JSON in SQLite.
- **Transaction mode** uses the original transaction-specific validation rules.

Run it from this folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app runs locally unless you deploy it separately. Generic mode accepts arbitrary readable CSV schemas, but validation rules must be configured to suit the dataset; it cannot infer all business meaning automatically.
