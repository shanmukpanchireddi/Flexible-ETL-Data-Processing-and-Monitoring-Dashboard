CREATE TABLE dim_currency (
    currency_key INTEGER PRIMARY KEY,
    currency_code TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_run (
    run_key INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_transactions (
    transaction_id TEXT PRIMARY KEY,
    currency_key INTEGER NOT NULL,
    run_key INTEGER NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (currency_key) REFERENCES dim_currency(currency_key),
    FOREIGN KEY (run_key) REFERENCES dim_run(run_key)
);
