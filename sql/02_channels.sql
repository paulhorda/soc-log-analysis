WITH traffic AS (
    SELECT channel, COUNT(*) AS sessions FROM sessions GROUP BY channel
), sales AS (
    SELECT channel, COUNT(*) AS orders, COUNT(DISTINCT session_id) AS purchasing_sessions,
           SUM(net_cents) AS net_cents, SUM(refund_cents) AS refund_cents
    FROM order_revenue GROUP BY channel
)
SELECT t.channel, t.sessions, COALESCE(s.orders,0) AS orders,
       COALESCE(s.purchasing_sessions,0) AS purchasing_sessions,
       ROUND(100.0 * COALESCE(s.purchasing_sessions,0) / t.sessions,2) AS conversion_pct,
       COALESCE(s.net_cents,0) AS net_cents,
       ROUND(1.0 * COALESCE(s.net_cents,0) / t.sessions,2) AS revenue_per_session_cents
FROM traffic t LEFT JOIN sales s USING(channel)
ORDER BY net_cents DESC, t.channel;
