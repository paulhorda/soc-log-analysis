"""Deterministic fictional retail data. No API, scraped records, or personal data."""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {
    'customers': ['customer_id'],
    'products': ['product_id', 'category', 'price_cents'],
    'sessions': ['session_id', 'customer_id', 'started_at', 'channel'],
    'orders': ['order_id', 'session_id', 'status'],
    'order_items': ['item_id', 'order_id', 'product_id', 'quantity', 'unit_price_cents'],
    'refunds': ['refund_id', 'item_id', 'amount_cents'],
}


def generate(destination=ROOT / 'data', seed=42):
    rng = random.Random(seed)
    data = {table: [] for table in HEADERS}
    data['customers'] = [[f'C{i:04}'] for i in range(1, 1201)]
    categories = ['Home', 'Electronics', 'Office', 'Outdoors']
    data['products'] = [[f'P{i:03}', categories[(i-1) % 4], rng.randrange(9, 150) * 100] for i in range(1, 25)]
    channels = ['organic', 'paid_search', 'email', 'direct']
    probability = {'organic': .16, 'paid_search': .10, 'email': .27, 'direct': .18}
    start = datetime(2026, 7, 1)
    for day in range(92):
        when = start + timedelta(days=day)
        for _ in range(rng.randint(80, 120)):
            channel = rng.choices(channels, weights=[35, 35, 12, 18])[0]
            # Email draws from a smaller recurring audience; this confounds channel comparisons.
            customer = rng.choice(data['customers'][:300] if channel == 'email' else data['customers'])[0]
            session = f'S{len(data["sessions"])+1:05}'
            timestamp = when + timedelta(seconds=rng.randrange(86400))
            data['sessions'].append([session, customer, timestamp.isoformat()+'Z', channel])
            seasonal = .75 if when.month == 9 and channel == 'paid_search' else 1
            if rng.random() >= probability[channel] * seasonal:
                continue
            for _ in range(2 if rng.random() < .09 else 1):
                order = f'O{len(data["orders"])+1:05}'
                status = 'cancelled' if rng.random() < .05 else 'completed'
                data['orders'].append([order, session, status])
                for product in rng.sample(data['products'], rng.randint(1, 3)):
                    item = f'I{len(data["order_items"])+1:05}'
                    quantity = rng.randint(1, 2)
                    data['order_items'].append([item, order, product[0], quantity, product[2]])
                    refund_rate = .15 if product[1] == 'Electronics' else .04
                    if status == 'completed' and rng.random() < refund_rate:
                        amount = product[2]  # One unit refunded; sometimes as two partial transactions.
                        parts = [amount // 2, amount - amount // 2] if rng.random() < .3 else [amount]
                        for part in parts:
                            data['refunds'].append([f'R{len(data["refunds"])+1:05}', item, part])
    destination.mkdir(parents=True, exist_ok=True)
    for table, rows in data.items():
        with (destination / f'{table}.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(HEADERS[table])
            writer.writerows(rows)
    return {table: len(rows) for table, rows in data.items()}


if __name__ == '__main__':
    print(generate())
