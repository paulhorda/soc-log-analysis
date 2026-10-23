WITH traffic AS (
    SELECT SUBSTR(started_at,1,7) AS month, COUNT(*) AS sessions FROM sessions GROUP BY month
), sales AS (
    SELECT SUBSTR(started_at,1,7) AS month, COUNT(*) AS orders,
           COUNT(DISTINCT session_id) AS purchasing_sessions,
           SUM(net_cents) AS net_cents, SUM(refund_cents) AS refund_cents
    FROM order_revenue GROUP BY month
), joined AS (
    SELECT t.month, t.sessions, COALESCE(s.orders,0) AS orders,
           COALESCE(s.net_cents,0) AS net_cents, COALESCE(s.refund_cents,0) AS refund_cents,
           ROUND(100.0 * COALESCE(s.purchasing_sessions,0) / t.sessions,2) AS conversion_pct
    FROM traffic t LEFT JOIN sales s USING(month)
)
SELECT *, ROUND(100.0 * (net_cents - LAG(net_cents) OVER(ORDER BY month)) /
               NULLIF(LAG(net_cents) OVER(ORDER BY month),0),2) AS revenue_change_pct
FROM joined ORDER BY month;
