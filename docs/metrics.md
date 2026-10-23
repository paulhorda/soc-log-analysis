# Data model and metric dictionary

| Table | Grain | Key |
|---|---|---|
| customers | One fictional identified visitor | customer_id |
| products | One product with a reference price | product_id |
| sessions | One visit with an attributed channel | session_id |
| orders | One order; several may belong to one visit | order_id |
| order_items | One product line with the transaction price | item_id |
| refunds | One partial refund transaction on a line | refund_id |

All sample timestamps are UTC. Every session has an identified customer, unlike most real web datasets. Order time is simplified to session time. Revenue is in EUR cents.

| Metric | Definition | Boundary |
|---|---|---|
| Purchasing sessions | Distinct session IDs with at least one completed order | Cancelled orders excluded; fully refunded completed orders still count as purchases |
| Session conversion | Purchasing sessions / all sessions | Undefined for no sessions |
| Gross item revenue | Sum(quantity × unit price) on completed orders | No tax, shipping or discounts |
| Net item revenue | Gross item revenue − refunds | Not profit or cash flow; refunds attributed to original purchase period |
| Net AOV | Net item revenue / completed orders | Zero-value fully refunded orders remain in denominator |
| Refund-value share | Refund value / gross item revenue | A value ratio, not percentage of returned orders |
| Revenue per session | Net item revenue / all sessions | No acquisition cost, so not ROI |
| Cohort | Month of first completed purchase observed in sample | Lifetime acquisition date unknown |
| Cohort retention | Cohort customers buying in month N / original cohort size | Distinct customers; repeat purchases within a month count once |

## Validation

SQLite enforces unique primary keys, foreign keys, positive quantities and amounts, and known statuses/channels. The pipeline additionally rejects refunds exceeding line value, refunds on cancelled orders, orders without items, and timestamps SQLite cannot parse or that lack the UTC `Z` suffix. It is a controlled-sample loader, not a general CSV cleansing service.

## Assumptions to revisit with real data

Identity stitching, timezone boundaries, attribution windows, partial refunds, cancelled transactions, late-arriving events and changing product prices all need explicit business agreement. Currencies must be normalized before aggregation. A calendar table should define completely missing periods in a production cohort analysis.
