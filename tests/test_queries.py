import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from analyze import load, query, run
from generate_logs import generate


def event(index, seconds, user='demo', ip='203.0.113.10', outcome='failure', service='vpn'):
    timestamp = datetime(2026, 9, 15, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return {'event_id': f'E{index:03}', 'timestamp': timestamp.isoformat().replace('+00:00', 'Z'),
            'user': user, 'source_ip': ip, 'outcome': outcome, 'service': service}


def results(events, filename):
    with sqlite3.connect(':memory:') as db:
        load(events, db)
        return query(db, filename)[1]


class QueryTests(unittest.TestCase):
    def test_failure_threshold_includes_ten_minute_boundary(self):
        rows = results([event(i, i*150) for i in range(5)], '03_failure_bursts.sql')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['failures_in_window'], 5)
        self.assertEqual(results([event(i, i*151) for i in range(5)], '03_failure_bursts.sql'), [])

    def test_multiple_accounts_counts_distinct_users(self):
        self.assertEqual(results([event(i, i) for i in range(8)], '04_multiple_users.sql'), [])
        rows = results([event(i, i, user=f'u{i}') for i in range(6)], '04_multiple_users.sql')
        self.assertEqual(rows[0]['users_in_window'], 6)

    def test_services_and_sources_stay_separate(self):
        self.assertEqual(results([event(i,i,service='vpn' if i<3 else 'ssh') for i in range(5)], '03_failure_bursts.sql'), [])
        self.assertEqual(results([event(i,i,ip=f'203.0.113.{i}') for i in range(5)], '03_failure_bursts.sql'), [])

    def test_success_must_follow_failures_for_same_account(self):
        failures = [event(i,i*60) for i in range(5)]
        rows = results(failures+[event(9,900,outcome='success')], '05_success_after_failures.sql')
        self.assertEqual(rows[0]['preceding_failures'], 5)
        self.assertEqual(results(failures+[event(9,901,outcome='success')], '05_success_after_failures.sql'), [])
        self.assertEqual(results(failures+[event(9,900,user='other',outcome='success')], '05_success_after_failures.sql'), [])

    def test_equal_timestamp_does_not_prove_failure_preceded_success(self):
        rows = results([event(i,0) for i in range(5)]+[event(9,0,outcome='success')], '05_success_after_failures.sql')
        self.assertEqual(rows, [])

    def test_duplicate_id_fails_import(self):
        with self.assertRaises(sqlite3.IntegrityError):
            results([event(1,0),event(1,0)], '01_services.sql')

    def test_invalid_timestamp_and_outcome_fail_import(self):
        bad = event(1,0)
        bad['timestamp'] = '2026-09-15T12:00:00'
        with self.assertRaises(ValueError):
            results([bad], '01_services.sql')
        with self.assertRaises(sqlite3.IntegrityError):
            results([event(1,0,outcome='unknown')], '01_services.sql')

    def test_canonical_ipv6_and_input_order(self):
        events = [event(i,i,ip='2001:db8::1' if i%2 else '2001:0db8:0:0:0:0:0:1') for i in range(5)]
        self.assertEqual(results(events, '03_failure_bursts.sql'), results(list(reversed(events)), '03_failure_bursts.sql'))
        self.assertEqual(len(results(events, '03_failure_bursts.sql')), 1)

    def test_service_counts_reconcile(self):
        rows = results([event(1,0), event(2,5,outcome='success'), event(3,8,outcome='success')], '01_services.sql')
        self.assertEqual((rows[0]['events'], rows[0]['successes'], rows[0]['failures']), (3,2,1))
        self.assertEqual(rows[0]['failure_pct'], 33.33)

    def test_empty_file_still_produces_csv_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'empty.jsonl').write_text('')
            result = run(root/'empty.jsonl', root/'reports')
            self.assertEqual(result['events'], 0)
            self.assertTrue((root/'reports/services.csv').read_text().startswith('service,events,'))

    def test_fixture_results_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate(root/'data')
            first = run(root/'data/auth_events.jsonl', root/'first')
            self.assertEqual(first['events'], 1231)
            self.assertEqual(len(first['results']['failure_bursts']), 6)
            self.assertEqual(len(first['results']['multiple_users']), 3)
            success = first['results']['success_after_failures']
            self.assertEqual([(row['success_event_id'],row['preceding_failures']) for row in success], [('EVT-01209',8)])
            (root/'data/scenario_labels.json').unlink()
            run(root/'data/auth_events.jsonl', root/'second')
            for file in (root/'first').iterdir():
                self.assertEqual(file.read_bytes(), (root/'second'/file.name).read_bytes())


if __name__ == '__main__':
    unittest.main()
