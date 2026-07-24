-- Phase 5 business queries — run against the loaded MySQL warehouse.
-- These queries use only ANSI-standard SQL that both Postgres and MySQL
-- support (SUM/AVG/ROUND/NULLIF/GROUP BY/JOIN), so no syntax changes were
-- needed beyond this header comment.

-- 1. Total revenue, profit, margin, basket value by week
SELECT week_no,
       SUM(sales_value) AS revenue,
       SUM(estimated_profit) AS profit,
       ROUND(AVG(profit_margin_pct), 2) AS avg_margin_pct,
       ROUND(AVG(basket_value), 2) AS avg_basket_value
FROM fact_transactions
GROUP BY week_no
ORDER BY week_no;

-- 2. Category (department) performance
SELECT p.department,
       SUM(t.sales_value) AS revenue,
       SUM(t.estimated_profit) AS profit,
       ROUND(100.0 * SUM(t.estimated_profit) / NULLIF(SUM(t.sales_value),0), 2) AS margin_pct
FROM fact_transactions t
JOIN dim_products p ON p.product_id = t.product_id
GROUP BY p.department
ORDER BY revenue DESC;

-- 3. Brand performance
SELECT p.brand,
       SUM(t.sales_value) AS revenue,
       SUM(t.quantity) AS units_sold
FROM fact_transactions t
JOIN dim_products p ON p.product_id = t.product_id
GROUP BY p.brand
ORDER BY revenue DESC
LIMIT 20;

-- 4. Promotion effectiveness: revenue & units, promo vs non-promo
SELECT is_promo,
       COUNT(*) AS n_transactions,
       SUM(sales_value) AS revenue,
       SUM(quantity) AS units,
       ROUND(AVG(profit_margin_pct), 2) AS avg_margin_pct
FROM fact_transactions
GROUP BY is_promo;

-- 5. Coupon redemption rate by campaign (requires coupon_redempt loaded separately)
-- Adjust table name if you load coupon_redempt.csv as fact_coupon_redemptions
-- SELECT campaign, COUNT(*) AS redemptions FROM fact_coupon_redemptions GROUP BY campaign;

-- 6. Regional / store-level sales
SELECT store_id,
       SUM(sales_value) AS revenue,
       COUNT(DISTINCT basket_id) AS n_baskets
FROM fact_transactions
GROUP BY store_id
ORDER BY revenue DESC
LIMIT 20;

-- 7. High-revenue but low-margin products (candidates for repricing)
SELECT t.product_id, p.commodity_desc,
       SUM(t.sales_value) AS revenue,
       ROUND(AVG(t.profit_margin_pct), 2) AS avg_margin_pct
FROM fact_transactions t
JOIN dim_products p ON p.product_id = t.product_id
GROUP BY t.product_id, p.commodity_desc
HAVING SUM(t.sales_value) > 1000
ORDER BY avg_margin_pct ASC
LIMIT 20;

-- 8. Household purchase frequency distribution
SELECT household_purchase_frequency, COUNT(DISTINCT household_key) AS n_households
FROM fact_transactions
GROUP BY household_purchase_frequency
ORDER BY household_purchase_frequency;
