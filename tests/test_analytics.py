import csv
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from analyze import ROOT, load, query, run, validate
from generate_data import generate


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript((ROOT / 'sql/schema.sql').read_text())
        self.db.executescript('''
            INSERT INTO customers VALUES ('c1'),('c2');
            INSERT INTO products VALUES ('p1','Home',1000);
            INSERT INTO sessions VALUES ('s1','c1','2026-07-01T12:00:00Z','email'),
              ('s2','c2','2026-07-02T12:00:00Z','direct'),
              ('s3','c1','2026-08-01T12:00:00Z','email');
            INSERT INTO orders VALUES ('o1','s1','completed'),('o2','s1','completed'),('o3','s2','cancelled');
            INSERT INTO order_items VALUES ('i1','o1','p1',2,1000),('i2','o2','p1',1,1000),('i3','o3','p1',1,1000);
            INSERT INTO refunds VALUES ('r1','i1',300),('r2','i1',200);
        ''')

    def tearDown(self):
        self.db.close()

    def test_multiple_orders_do_not_inflate_session_conversion(self):
        result = query(self.db, '01_kpis.sql')[0]
        self.assertEqual(result['completed_orders'], 2)
        self.assertEqual(result['purchasing_sessions'], 1)
        self.assertEqual(result['conversion_pct'], 33.33)

    def test_refunds_do_not_multiply_gross_revenue(self):
        result = query(self.db, '01_kpis.sql')[0]
        self.assertEqual((result['gross_cents'], result['refund_cents'], result['net_cents']), (3000, 500, 2500))
        self.assertEqual(result['net_aov_cents'], 1250)

    def test_channel_without_completed_purchase_remains_visible(self):
        rows = {row['channel']: row for row in query(self.db, '02_channels.sql')}
        self.assertEqual(rows['direct']['conversion_pct'], 0)

    def test_observed_zero_retention_and_no_future_cohorts(self):
        rows = query(self.db, '04_cohorts.sql')
        self.assertEqual([(r['month_index'], r['retention_pct']) for r in rows], [(0, 100.0), (1, 0.0)])

    def test_refund_above_item_value_fails_validation(self):
        self.db.execute("INSERT INTO refunds VALUES ('r3','i1',1600)")
        with self.assertRaisesRegex(ValueError, 'refunds_above_item_value'):
            validate(self.db)

    def test_orphaned_order_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO orders VALUES ('missing','unknown','completed')")

    def test_empty_dataset_has_zero_counts_and_undefined_ratios(self):
        with sqlite3.connect(':memory:') as db:
            db.executescript((ROOT / 'sql/schema.sql').read_text())
            result = query(db, '01_kpis.sql')[0]
            self.assertEqual(result['net_cents'], 0)
            self.assertIsNone(result['conversion_pct'])

    def test_pipeline_is_reproducible_and_reconciles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate(root / 'data')
            first = run(root / 'data', root / 'one')
            generate(root / 'data')
            second = run(root / 'data', root / 'two')
            self.assertEqual(first, second)
            for path in (root / 'one').iterdir():
                self.assertEqual(path.read_bytes(), (root / 'two' / path.name).read_bytes())
            self.assertEqual(sum(r['net_cents'] for r in first['channels']), first['kpis'][0]['net_cents'])
            self.assertEqual(sum(r['net_cents'] for r in first['categories']), first['kpis'][0]['net_cents'])
            self.assertEqual(sum(r['net_cents'] for r in first['monthly']), first['kpis'][0]['net_cents'])


if __name__ == '__main__':
    unittest.main()
