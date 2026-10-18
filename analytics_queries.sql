-- total amount by currency
SELECT
    dim_currency.currency_code,
    SUM(fact_transactions.amount) AS total_amount
FROM fact_transactions
JOIN dim_currency
    ON fact_transactions.currency_key = dim_currency.currency_key
GROUP BY dim_currency.currency_code;

-- transaction count by currency
SELECT
    dim_currency.currency_code,
    COUNT(*) AS transaction_count
FROM fact_transactions
JOIN dim_currency
    ON fact_transactions.currency_key = dim_currency.currency_key
GROUP BY dim_currency.currency_code;

-- total amount by run
SELECT
    dim_run.run_id,
    SUM(fact_transactions.amount) AS total_amount
FROM fact_transactions
JOIN dim_run
    ON fact_transactions.run_key = dim_run.run_key
GROUP BY dim_run.run_id;

-- average transaction by currency

SELECT
    dim_currency.currency_code,
    AVG(fact_transactions.amount) AS average_amount
FROM fact_transactions
JOIN dim_currency
    ON fact_transactions.currency_key = dim_currency.currency_key
GROUP BY dim_currency.currency_code;

-- transaction count by run

SELECT
    dim_run.run_id,
    COUNT(*) AS transaction_count
FROM fact_transactions
JOIN dim_run
    ON fact_transactions.run_key = dim_run.run_key
GROUP BY dim_run.run_id;



-- verify fact table row count matches clean source row count
SELECT
    (SELECT COUNT(*) FROM clean_transactions) AS source_rows,
    (SELECT COUNT(*) FROM fact_transactions) AS fact_rows,
    (SELECT COUNT(*) FROM clean_transactions)
    -
    (SELECT COUNT(*) FROM fact_transactions) AS row_difference;