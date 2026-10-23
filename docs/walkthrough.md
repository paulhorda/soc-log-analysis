# Review walkthrough

1. Read the business question and the generated findings. Separate measured numbers from hypotheses.
2. Inspect `data/` and identify each table's grain. Explain why joining two refund rows directly to one item doubles gross revenue.
3. Read `sql/schema.sql`. Explain how `item_revenue` and `order_revenue` prevent that fan-out.
4. Compare completed orders and purchasing sessions. Explain why the latter belongs in conversion's numerator.
5. Read the cohort query. Explain why July-to-August retention is observable and September-to-October retention is not.
6. Run the tests. Change one refund to exceed its line value and confirm the loader rejects it; regenerate the data afterwards.
7. Change the seed in a separate experiment. Compare results without representing the fictional sample as real market behavior.

## Extensions requiring new evidence

- Import an openly licensed real dataset with provenance, consent and a documented schema mapping.
- Add spend and margin data before making acquisition-budget recommendations.
- Add a complete calendar table and explicit date filters for incomplete observation periods.
- Build a Power BI dashboard from the exported tables; no Power BI implementation is claimed in this version.

This lab was prepared with AI assistance. Reproduce it and explain its decisions before presenting it as evidence of your own practical understanding.
