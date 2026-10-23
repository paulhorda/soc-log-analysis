"""Load normalized authentication logs into SQLite and run investigation queries."""
import argparse
import csv
import hashlib
import ipaddress
import json
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(events, connection):
    connection.executescript((ROOT / 'sql/schema.sql').read_text())
    for event in events:
        for key in ('event_id', 'timestamp', 'user', 'source_ip', 'outcome', 'service'):
            if not isinstance(event.get(key), str) or not event[key].strip():
                raise ValueError(f'Missing or invalid {key}')
        if not event['timestamp'].endswith('Z'):
            raise ValueError('timestamp must end in Z (UTC)')
        timestamp = datetime.fromisoformat(event['timestamp'][:-1]+'+00:00')
        canonical_time = timestamp.isoformat(timespec='microseconds').replace('+00:00', 'Z')
        source = str(ipaddress.ip_address(event['source_ip']))
        connection.execute('INSERT INTO auth_events VALUES (?,?,?,?,?,?,?)',
                           (event['event_id'], canonical_time, timestamp.timestamp(), event['user'],
                            source, event['outcome'], event['service']))
    connection.commit()


def read_events(path):
    rows = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'Invalid JSON on line {line_number}') from exc
        if not isinstance(row, dict):
            raise ValueError(f'Expected an event object on line {line_number}')
        rows.append(row)
    return rows


def query(connection, name):
    cursor = connection.execute((ROOT / 'sql' / name).read_text())
    headers = [column[0] for column in cursor.description]
    return headers, [dict(zip(headers, row)) for row in cursor]


def table(headers, rows):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join('---' for _ in headers)+' |'] +
                     ['| '+' | '.join(cell(row[key]) for key in headers)+' |' for row in rows])


def run(input_path=ROOT / 'data/auth_events.jsonl', output=ROOT / 'reports'):
    events = read_events(input_path)
    output.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(':memory:') as db:
        load(events, db)
        result = {}
        for path in sorted((ROOT / 'sql').glob('[0-9]*.sql')):
            headers, rows = query(db, path.name)
            result[path.stem[3:]] = rows
            with (output / (path.stem[3:]+'.csv')).open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=headers, lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)
    summary = {'events': len(events), 'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(), 'results': result}
    (output / 'results.json').write_text(json.dumps(summary, indent=2)+'\n')
    lines = ['# Authentication log review', '', f'{len(events):,} generated lab events. Timestamps are UTC.', '',
             '## Services', '', table(['service', 'events', 'successes', 'failures', 'failure_pct', 'users', 'sources'], result['services']), '',
             '`failure_pct` is the share of authentication events that failed. It says nothing about the probability of an attack.', '',
             '## Sources with the most failures', '', table(['source_ip','service','failures','affected_users','first_failure','last_failure'], result['sources'][:5]), '',
             'The full list is in [sources.csv](sources.csv). Counts cover the whole input; the queries below use shorter windows.', '',
             '## Window matches', '',
             f'- [Repeated failures](failure_bursts.csv): {len(result["failure_bursts"])} qualifying windows.',
             f'- [Failures across accounts](multiple_users.csv): {len(result["multiple_users"])} qualifying windows.',
             f'- [Success after failures](success_after_failures.csv): {len(result["success_after_failures"])} matching success event(s).', '',
             'Windows overlap. These row counts are not counts of separate incidents.', '',
             '## Successful logins to review', '', table(['success_event_id','success_at','user','source_ip','preceding_failures'], result['success_after_failures']), '',
             'Start with the original event IDs, then check MFA, device details and user context. Those fields are absent from this sample.', '',
             '[Sample notes](../docs/notes.md) · [SQL queries](../sql/) · [All results](results.json)', '']
    (output / 'review.md').write_text('\n'.join(lines))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/auth_events.jsonl')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports')
    args = parser.parse_args()
    result = run(args.input, args.output)
    print(f'Analyzed {result["events"]} events. Results: {args.output}')
