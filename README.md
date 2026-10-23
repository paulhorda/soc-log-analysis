# Authentication log analysis

SQL queries for investigating failed logins and successful logins that follow them. Python loads a JSONL file into SQLite and saves the query results as CSV.

The sample contains 1,231 generated events. It is shared with [SOC Alert Triage Lab](https://github.com/paulhorda/soc-alert-triage-lab), so the two approaches can be compared.

## Queries

| File | Question |
|---|---|
| [01_services.sql](sql/01_services.sql) | How much activity does each service have? |
| [02_sources.sql](sql/02_sources.sql) | Which sources have the most failures, and how many accounts are involved? |
| [03_failure_bursts.sql](sql/03_failure_bursts.sql) | Are there five failures for one account and source within ten minutes? |
| [04_multiple_users.sql](sql/04_multiple_users.sql) | Does one source fail against six different accounts within ten minutes? |
| [05_success_after_failures.sql](sql/05_success_after_failures.sql) | Does a successful login follow at least five failures within fifteen minutes? |

Each query keeps services separate. Window queries return every qualifying window; they do not group matches into incidents or apply an alert cooldown.

## Run

Python 3.10 or later. No extra packages.

```bash
python3 src/generate_logs.py
python3 src/analyze.py
python3 -m unittest discover -s tests -v
```

[Read the results](reports/review.md) or open the CSV files in `reports/`.

For another file with the same fields:

```bash
python3 src/analyze.py --input events.jsonl --output local-results
```

Required fields: `event_id`, `timestamp` (UTC, ending in `Z`), `user`, `source_ip`, `outcome` (`success` or `failure`) and `service`. Duplicate IDs and invalid records fail the import. IPs and timestamps are normalized before grouping.

## Sample notes

There is a burst followed by a success, failures across several accounts, a stale service credential, and a slow sequence that the ten-minute queries miss. [Notes and limitations](docs/notes.md) explain each case.

The queries provide leads for an investigation. The sample has no MFA, device or session activity data to establish whether a login was unauthorized.
