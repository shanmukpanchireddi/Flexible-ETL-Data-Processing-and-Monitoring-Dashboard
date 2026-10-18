# Project 2 Model Design

## Purpose

This document explains the first analytical model layer built from the Project 1 DB-backed ETL pipeline.

Project 1 stores cleaned and rejected transaction data in SQLite.

Project 2 starts converting accepted transaction records into an analytics-friendly structure.

---

## Business process

The model represents accepted transaction activity produced by the Project 1 ETL pipeline.

Only clean transactions are modelled in the analytical layer.

Rejected rows remain part of the data-quality/audit layer and are not loaded into the fact table.

---

## Grain

One row in `fact_transactions` represents one accepted transaction from `clean_transactions`.

This is the central modelling rule.

The fact table should not mix transaction-level rows with run-level or currency-level summaries.

---

## Current model tables

### `fact_transactions`

Stores accepted transaction facts.

Current columns:

- `transaction_id`
- `amount`
- `currency_key`
- `run_key`

Measure:

- `amount`

Foreign-key-style references:

- `currency_key` links to `dim_currency`
- `run_key` links to `dim_run`

### `dim_currency`

Describes the transaction currency.

Current columns:

- `currency_key`
- `currency_code`

### `dim_run`

Describes the pipeline run that produced the transaction.

Current columns:

- `run_key`
- `run_id`

---

## Deferred dimension: `dim_date`

A `dim_date` table is intentionally deferred.

The current source data does not yet include a reliable transaction date in the cleaned SQLite output.

Adding `dim_date` before the source field exists would make the model look more complete than it actually is.

Future date modelling should be added when the pipeline includes a real transaction date or a clearly defined load date.

---

## Intended analytical questions

The current model should support questions such as:

1. What is the total transaction amount by currency?
2. How many accepted transactions exist by currency?
3. What is the total accepted transaction amount by pipeline run?
4. How many transactions were loaded per run?
5. Which currency has the highest accepted transaction total?

---

## Current implementation files

- `model_schema.sql` creates the analytical model tables.
- `model_load.sql` loads the model from Project 1 SQLite tables.
- `analytics_queries.sql` contains OLAP-style queries over the analytical model.

---

## Model boundary

This is a small local analytical model, not a production warehouse.

It is designed to demonstrate:

- grain definition
- fact vs dimension separation
- basic dimensional modelling
- SQL joins for reporting
- Project 1 to Project 2 progression
