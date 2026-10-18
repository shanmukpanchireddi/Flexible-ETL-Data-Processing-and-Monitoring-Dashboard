-- fact row count vs source row count
SELECT COUNT(*) AS fact_row_count
FROM fact_transactions;

SELECT COUNT(*) AS source_row_count
FROM clean_transactions;

-- dim_currency row count vs distinct source currency count
SELECT COUNT(*) AS dim_currency_count
FROM dim_currency;

SELECT COUNT(DISTINCT currency) AS source_currency_count
FROM clean_transactions;

-- dim_run row count vs distinct source run count
SELECT COUNT(*) AS dim_run_count
FROM dim_run;

SELECT COUNT(DISTINCT run_id) AS source_run_count
FROM clean_transactions;

-- rerun check
SELECT COUNT(*) AS fact_row_rerun_count
FROM fact_transactions;

SELECT COUNT(*) AS dim_currency_rerun_count
FROM dim_currency;

SELECT COUNT(*) AS dim_run_rerun_count
FROM dim_run;