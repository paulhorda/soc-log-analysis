"""Load CSVs into SQLite, validate grains, execute SQL, and publish reviewable outputs."""
import csv
import html
import json
import sqlite3
from pathlib import Path

from generate_data import HEADERS

ROOT = Path(__file__).resolve().parents[1]


def load(data_dir, connection):
    connection.executescript((ROOT / 'sql/schema.sql').read_text())
    for table, headers in HEADERS.items():
        with (data_dir / f'{table}.csv').open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != headers:
                raise ValueError(f'Unexpected columns in {table}')
            connection.executemany(
                f'INSERT INTO {table} VALUES ({",".join("?" for _ in headers)})',
                ([row[column] for column in headers] for row in reader),
            )
    validate(connection)
    connection.commit()


def validate(connection):
    checks = {
        'orders_without_items': 'SELECT COUNT(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id=o.order_id)',
        'refunds_above_item_value': '''SELECT COUNT(*) FROM (SELECT i.item_id FROM order_items i JOIN refunds r USING(item_id)
            GROUP BY i.item_id HAVING SUM(r.amount_cents)>i.quantity*i.unit_price_cents)''',
        'refunds_on_cancelled_orders': "SELECT COUNT(*) FROM refunds JOIN order_items USING(item_id) JOIN orders USING(order_id) WHERE status='cancelled'",
        'invalid_timestamps': "SELECT COUNT(*) FROM sessions WHERE datetime(started_at) IS NULL OR substr(started_at,-1)!='Z'",
    }
    for name, sql in checks.items():
        count = connection.execute(sql).fetchone()[0]
        if count:
            raise ValueError(f'{name}: {count}')
    if connection.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('Foreign key violations')
    return list(checks) + ['foreign_keys', 'primary_keys', 'positive_amounts', 'valid_statuses']


def query(connection, filename):
    cursor = connection.execute((ROOT / 'sql' / filename).read_text())
    return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor]


def dashboard(kpi, channels, monthly):
    """Static, self-contained SVG with text equivalents in the Markdown report."""
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="650" viewBox="0 0 1080 650" role="img" aria-labelledby="title desc">',
           '<title id="title">Retail analytics: synthetic sample</title>',
           '<desc id="desc">Revenue and purchasing-session conversion by channel, with monthly net revenue. Source tables accompany this chart.</desc>',
           '<rect width="1080" height="650" rx="20" fill="#0b1220"/>',
           '<g font-family="Arial, sans-serif" fill="#e7edf5">',
           '<text x="40" y="49" font-size="14" fill="#5eead4">DATA ANALYTICS / SQL + PYTHON</text>',
           '<text x="40" y="90" font-size="30" font-weight="700">From visits to net revenue</text>',
           '<text x="40" y="117" font-size="14" fill="#a8b8cf">Synthetic retail data · July–September 2026 · EUR</text>']
    cards = [('NET REVENUE', f'€{kpi["net_cents"]/100:,.0f}'), ('SESSION CONVERSION', f'{kpi["conversion_pct"]}%'), ('COMPLETED ORDERS', f'{kpi["completed_orders"]:,}')]
    for x, (label, value) in zip([40, 380, 720], cards):
        out += [f'<rect x="{x}" y="148" width="320" height="102" rx="10" fill="#162236"/>',
                f'<text x="{x+20}" y="179" font-size="12" fill="#a8b8cf">{label}</text>',
                f'<text x="{x+20}" y="220" font-size="30" font-weight="700">{value}</text>']
    out += ['<text x="40" y="295" font-size="19" font-weight="700">Channel conversion</text>',
            '<text x="585" y="295" font-size="19" font-weight="700">Monthly net revenue</text>']
    max_conversion = max(row['conversion_pct'] for row in channels) or 1
    for i, row in enumerate(channels):
        y = 332+i*55
        out += [f'<text x="40" y="{y}" font-size="14">{html.escape(row["channel"])}</text>',
                f'<rect x="155" y="{y-15}" width="{260*row["conversion_pct"]/max_conversion:.1f}" height="22" rx="4" fill="#2dd4bf"/>',
                f'<text x="430" y="{y}" font-size="14">{row["conversion_pct"]}%</text>']
    maximum = max(row['net_cents'] for row in monthly) or 1
    for i, row in enumerate(monthly):
        x = 600+i*145
        height = 160*row['net_cents']/maximum
        out += [f'<rect x="{x}" y="{510-height:.1f}" width="90" height="{height:.1f}" rx="5" fill="#60a5fa"/>',
                f'<text x="{x+45}" y="{498-height:.1f}" text-anchor="middle" font-size="13">€{row["net_cents"]/100:,.0f}</text>',
                f'<text x="{x+45}" y="538" text-anchor="middle" font-size="13">{row["month"]}</text>']
    out += ['<text x="40" y="590" font-size="14" fill="#a8b8cf">Conversion = unique purchasing sessions / all sessions. Multiple orders do not inflate it.</text>',
            '<text x="40" y="617" font-size="13" fill="#a8b8cf">Fictional scenario. Channel differences are descriptive; no causal or ROI claims.</text>', '</g></svg>']
    return '\n'.join(out)+'\n'


def run(data_dir=ROOT / 'data', output=ROOT / 'reports'):
    output.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(':memory:') as db:
        load(data_dir, db)
        result = {path.stem[3:]: query(db, path.name) for path in sorted((ROOT / 'sql').glob('[0-9]*.sql'))}
        for name, rows in result.items():
            with (output / f'{name}.csv').open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [], lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)
        kpi = result['kpis'][0]
        quality = {'status': 'passed', 'checks': validate(db), 'table_rows': {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in HEADERS}}
        (output / 'quality.json').write_text(json.dumps(quality, indent=2)+'\n')
        (output / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
        (output / 'dashboard.svg').write_text(dashboard(kpi, result['channels'], result['monthly']))
        top = max(result['channels'], key=lambda row: row['conversion_pct'])
        refund = max(result['categories'], key=lambda row: row['refund_value_pct'])
        report = f'''# Retail decision brief

> Reproducible synthetic scenario. These are calculated lab results, not a real company's performance.

![Dashboard](dashboard.svg)

## Question
Which channels convert visits into purchases, how does net revenue change, and where should an analyst investigate next?

## Measured results
- {kpi['sessions']:,} sessions; {kpi['purchasing_sessions']:,} purchasing sessions; {kpi['completed_orders']:,} completed orders.
- Purchasing-session conversion: **{kpi['conversion_pct']}%**.
- Net item revenue after refunds: **€{kpi['net_cents']/100:,.2f}**.
- Net average completed-order value: **€{kpi['net_aov_cents']/100:,.2f}**.
- **{top['channel']}** has the highest observed conversion ({top['conversion_pct']}%).
- **{refund['category']}** has the highest refund-value share ({refund['refund_value_pct']}% of category gross revenue).

## Interpretation and next decisions
1. Investigate channel conversion by new/returning customer and campaign before changing budget. Email samples a smaller recurring audience in the generator; higher conversion is not proof of better acquisition.
2. Inspect Electronics refund reasons and product-level patterns. The sample intentionally assigns a higher refund probability to this category; no causal product-quality conclusion follows.
3. Use the monthly table to separate traffic from conversion and revenue changes. Paid-search purchase probability is deliberately reduced in September. Treat this as an investigation exercise, not a discovered market trend.
4. Request marketing spend, margin, campaign assignment and refund timestamps before estimating ROI, profit or cash flow. None are present here.

## Definitions and caveats
- Conversion counts distinct purchasing sessions, not orders divided by visits.
- Revenue excludes cancelled orders and aggregates refunds before joining to avoid duplicated revenue.
- Refunds are attributed back to the purchase period. There are no refund dates, taxes, shipping or discounts.
- Cohorts use first purchase observed in this three-month sample; earlier lifetime purchases are unknown. Future months are not presented as zero retention.
- The identified visitors in this simplified dataset are not a realistic model of anonymous web traffic.

## Evidence
[SQL](../sql/) · [Metric dictionary](../docs/metrics.md) · [Quality checks](quality.json) · [All result tables](summary.json)
'''
        (output / 'findings.md').write_text(report)
    return result


if __name__ == '__main__':
    print(json.dumps(run()['kpis'][0], indent=2))
