SELECT p.category, COUNT(DISTINCT i.order_id) AS orders,
       SUM(i.quantity) AS units, SUM(i.gross_cents) AS gross_cents,
       SUM(i.refund_cents) AS refund_cents, SUM(i.net_cents) AS net_cents,
       ROUND(100.0*SUM(i.refund_cents)/NULLIF(SUM(i.gross_cents),0),2) AS refund_value_pct
FROM item_revenue i JOIN products p USING(product_id)
GROUP BY p.category ORDER BY net_cents DESC, p.category;
