-- Observed first-purchase cohort, not account signup or lifetime acquisition.
WITH purchases AS (
    SELECT DISTINCT customer_id, SUBSTR(started_at,1,7) AS purchase_month FROM order_revenue
), first_purchase AS (
    SELECT customer_id, MIN(purchase_month) AS cohort FROM purchases GROUP BY customer_id
), sizes AS (
    SELECT cohort, COUNT(*) AS cohort_size FROM first_purchase GROUP BY cohort
), months AS (
    SELECT DISTINCT SUBSTR(started_at,1,7) AS month FROM sessions
), activity AS (
    SELECT f.cohort, p.purchase_month, COUNT(*) AS active_customers
    FROM first_purchase f JOIN purchases p USING(customer_id) GROUP BY f.cohort, p.purchase_month
)
SELECT s.cohort, m.month AS activity_month,
       (CAST(SUBSTR(m.month,1,4) AS INT)-CAST(SUBSTR(s.cohort,1,4) AS INT))*12
       + CAST(SUBSTR(m.month,6,2) AS INT)-CAST(SUBSTR(s.cohort,6,2) AS INT) AS month_index,
       s.cohort_size, COALESCE(a.active_customers,0) AS active_customers,
       ROUND(100.0 * COALESCE(a.active_customers,0)/s.cohort_size,2) AS retention_pct
FROM sizes s CROSS JOIN months m
LEFT JOIN activity a ON a.cohort=s.cohort AND a.purchase_month=m.month
WHERE m.month>=s.cohort ORDER BY s.cohort, m.month;
