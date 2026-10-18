-- populate dim_currency
INSERT OR IGNORE INTO dim_currency (currency_code)
SELECT DISTINCT currency
FROM clean_transactions;

-- populate dim_run
INSERT OR IGNORE INTO dim_run (run_id)
SELECT DISTINCT run_id
FROM clean_transactions;

-- verify dim_currency
SELECT COUNT(*) AS dim_currency_rows
FROM dim_currency;

SELECT COUNT(DISTINCT currency) AS source_currency_rows
FROM clean_transactions;

-- verify dim_run
SELECT COUNT(*) AS dim_run_rows
FROM dim_run;

SELECT COUNT(DISTINCT run_id) AS source_run_rows
FROM clean_transactions;

-- populate fact_transactions
INSERT OR IGNORE INTO fact_transactions (transaction_id, currency_key, run_key, amount)
SELECT
    clean_transactions.transaction_id,
    dim_currency.currency_key,
    dim_run.run_key,
    clean_transactions.amount
FROM clean_transactions
JOIN dim_currency
    ON clean_transactions.currency = dim_currency.currency_code
JOIN dim_run
    ON clean_transactions.run_id = dim_run.run_id;

-- verify fact_transactions
SELECT COUNT(*) AS fact_transaction_rows
FROM fact_transactions;

SELECT COUNT(*) AS source_transaction_rows
FROM clean_transactions;
