SELECT
    (SELECT COUNT(*) FROM sessions) AS sessions,
    COUNT(DISTINCT session_id) AS purchasing_sessions,
    COUNT(*) AS completed_orders,
    COUNT(DISTINCT customer_id) AS purchasing_customers,
    COALESCE(SUM(gross_cents),0) AS gross_cents,
    COALESCE(SUM(refund_cents),0) AS refund_cents,
    COALESCE(SUM(net_cents),0) AS net_cents,
    ROUND(100.0 * COUNT(DISTINCT session_id) / NULLIF((SELECT COUNT(*) FROM sessions),0),2) AS conversion_pct,
    ROUND(1.0 * SUM(net_cents) / NULLIF(COUNT(*),0),2) AS net_aov_cents
FROM order_revenue;
