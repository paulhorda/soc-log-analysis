PRAGMA foreign_keys = ON;
CREATE TABLE customers (customer_id TEXT PRIMARY KEY);
CREATE TABLE products (product_id TEXT PRIMARY KEY, category TEXT NOT NULL, price_cents INTEGER NOT NULL CHECK(price_cents > 0));
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers,
    started_at TEXT NOT NULL,
    channel TEXT NOT NULL CHECK(channel IN ('organic','paid_search','email','direct'))
);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions,
    status TEXT NOT NULL CHECK(status IN ('completed','cancelled'))
);
CREATE TABLE order_items (
    item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders,
    product_id TEXT NOT NULL REFERENCES products,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0)
);
CREATE TABLE refunds (
    refund_id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL REFERENCES order_items,
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0)
);
-- Aggregate refunds BEFORE joining to items: multiple refunds must not multiply revenue.
CREATE VIEW item_revenue AS
WITH refund_totals AS (
    SELECT item_id, SUM(amount_cents) AS refund_cents FROM refunds GROUP BY item_id
)
SELECT i.*, i.quantity * i.unit_price_cents AS gross_cents,
       COALESCE(r.refund_cents, 0) AS refund_cents,
       i.quantity * i.unit_price_cents - COALESCE(r.refund_cents, 0) AS net_cents
FROM order_items i
LEFT JOIN refund_totals r USING(item_id)
JOIN orders o USING(order_id)
WHERE o.status = 'completed';
-- Exactly one row per completed order; currency calculations stay in integer cents.
CREATE VIEW order_revenue AS
SELECT o.order_id, o.session_id, s.customer_id, s.started_at, s.channel,
       SUM(i.gross_cents) AS gross_cents, SUM(i.refund_cents) AS refund_cents,
       SUM(i.net_cents) AS net_cents
FROM orders o JOIN sessions s USING(session_id) JOIN item_revenue i USING(order_id)
GROUP BY o.order_id, o.session_id, s.customer_id, s.started_at, s.channel;
