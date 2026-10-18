-- =========================================================
-- etl-mini-pipeline: SQL Query Pack
-- =========================================================
-- Purpose:
-- - inspect data loaded into SQLite
-- - verify clean and rejected loading after pipeline runs
-- - provide SQL proof for Project 1 behaviour
--
-- Tables:
-- - clean_transactions(transaction_id, amount, currency, run_id)
-- - rejected_transactions(transaction_id, amount, currency, error_reason, run_id)
-- =========================================================


-- =========================================================
-- 1. TABLE INSPECTION
-- =========================================================

SELECT
    COUNT(*) AS total_clean_rows
FROM clean_transactions;

SELECT
    COUNT(*) AS total_rejected_rows
FROM rejected_transactions;

SELECT
    transaction_id,
    amount,
    currency,
    run_id
FROM clean_transactions
LIMIT 10;

SELECT
    transaction_id,
    amount,
    currency,
    error_reason,
    run_id
FROM rejected_transactions
LIMIT 10;


-- =========================================================
-- 2. CLEAN TRANSACTION VERIFICATION
-- =========================================================

SELECT
    currency,
    COUNT(*) AS row_count
FROM clean_transactions
GROUP BY currency
ORDER BY row_count DESC;

SELECT
    currency,
    SUM(amount) AS total_amount
FROM clean_transactions
GROUP BY currency
ORDER BY total_amount DESC;

SELECT
    run_id,
    COUNT(*) AS row_count,
    SUM(amount) AS total_amount
FROM clean_transactions
GROUP BY run_id
ORDER BY run_id;

-- Duplicate check on clean-table uniqueness key.
-- Expected result: zero rows if rerun safety is holding.
SELECT
    transaction_id,
    run_id,
    COUNT(*) AS duplicate_count
FROM clean_transactions
GROUP BY transaction_id, run_id
HAVING COUNT(*) > 1;


-- =========================================================
-- 3. WHERE VS HAVING BASELINE
-- =========================================================

-- WHERE filters rows before grouping.
SELECT
    currency,
    COUNT(*) AS row_count
FROM clean_transactions
WHERE currency = 'GBP'
GROUP BY currency;

-- HAVING filters groups after grouping.
SELECT
    currency,
    COUNT(*) AS row_count
FROM clean_transactions
GROUP BY currency
HAVING COUNT(*) >= 1;


-- =========================================================
-- 4. STRUCTURED REPORTING PATTERNS
-- =========================================================

WITH currency_totals AS (
    SELECT
        currency,
        SUM(amount) AS total_amount
    FROM clean_transactions
    WHERE run_id = 'run_001'
    GROUP BY currency
)
SELECT
    currency,
    total_amount
FROM currency_totals
WHERE total_amount > 50
ORDER BY total_amount DESC;

WITH currency_totals AS (
    SELECT
        currency,
        COUNT(*) AS row_count,
        SUM(amount) AS total_amount
    FROM clean_transactions
    WHERE run_id = 'run_001'
    GROUP BY currency
)
SELECT
    currency,
    row_count,
    total_amount
FROM currency_totals
WHERE total_amount > 50
ORDER BY total_amount DESC;

SELECT
    currency,
    SUM(amount) AS total_amount,
    CASE
        WHEN SUM(amount) > 50 THEN 'high'
        ELSE 'low'
    END AS amount_band
FROM clean_transactions
WHERE run_id = 'run_001'
GROUP BY currency
ORDER BY total_amount DESC;

SELECT
    currency,
    COUNT(*) AS row_count,
    SUM(amount) AS total_amount,
    CASE
        WHEN SUM(amount) > 50 THEN 'high'
        ELSE 'low'
    END AS amount_band
FROM clean_transactions
WHERE run_id = 'run_001'
GROUP BY currency
ORDER BY total_amount DESC;

SELECT
    currency,
    row_count,
    total_amount,
    CASE
        WHEN total_amount > 50 THEN 'high'
        ELSE 'low'
    END AS amount_band
FROM (
    SELECT
        currency,
        COUNT(*) AS row_count,
        SUM(amount) AS total_amount
    FROM clean_transactions
    WHERE run_id = 'run_001'
    GROUP BY currency
) AS currency_totals
ORDER BY total_amount DESC;


-- =========================================================
-- 5. REJECTED TRANSACTION VERIFICATION
-- =========================================================

SELECT
    run_id,
    COUNT(*) AS rejected_row_count
FROM rejected_transactions
GROUP BY run_id
ORDER BY run_id;

SELECT
    run_id,
    error_reason,
    COUNT(*) AS rejected_reason_count
FROM rejected_transactions
GROUP BY run_id, error_reason
ORDER BY run_id, rejected_reason_count DESC;

-- Duplicate check on rejected-table uniqueness key.
-- Expected result: zero rows if rerun safety is holding.
SELECT
    transaction_id,
    error_reason,
    run_id,
    COUNT(*) AS duplicate_count
FROM rejected_transactions
GROUP BY transaction_id, error_reason, run_id
HAVING COUNT(*) > 1;


-- =========================================================
-- 6. RECONCILIATION / COMPARISON
-- =========================================================

WITH clean_count AS (
    SELECT
        run_id,
        COUNT(*) AS clean_row_count
    FROM clean_transactions
    GROUP BY run_id
),
rejected_count AS (
    SELECT
        run_id,
        COUNT(*) AS rejected_row_count
    FROM rejected_transactions
    GROUP BY run_id
)
SELECT
    c.run_id,
    c.clean_row_count,
    COALESCE(r.rejected_row_count, 0) AS rejected_row_count,
    c.clean_row_count + COALESCE(r.rejected_row_count, 0) AS total_processed_rows
FROM clean_count AS c
LEFT JOIN rejected_count AS r
    ON c.run_id = r.run_id
ORDER BY c.run_id;


-- =========================================================
-- 7. FUTURE RECONCILIATION PLACEHOLDERS
-- =========================================================

-- Future improvement:
-- Compare clean + rejected DB counts against source input row count.

-- Future improvement:
-- Verify run-level totals against source file expectations.
