# Authentication log review

1,231 generated lab events. Timestamps are UTC.

## Services

| service | events | successes | failures | failure_pct | users | sources |
| --- | --- | --- | --- | --- | --- | --- |
| vpn | 1225 | 1158 | 67 | 5.47 | 137 | 203 |
| backup-console | 6 | 0 | 6 | 100.0 | 1 | 1 |

`failure_pct` is the share of authentication events that failed. It says nothing about the probability of an attack.

## Sources with the most failures

| source_ip | service | failures | affected_users | first_failure | last_failure |
| --- | --- | --- | --- | --- | --- |
| 192.0.2.90 | vpn | 8 | 8 | 2026-09-15T18:00:00.000000Z | 2026-09-15T20:20:00.000000Z |
| 198.51.100.23 | vpn | 8 | 8 | 2026-09-15T16:00:00.000000Z | 2026-09-15T16:07:00.000000Z |
| 203.0.113.42 | vpn | 8 | 1 | 2026-09-15T14:00:00.000000Z | 2026-09-15T14:07:00.000000Z |
| 10.20.0.250 | backup-console | 6 | 1 | 2026-09-15T17:00:00.000000Z | 2026-09-15T17:05:00.000000Z |
| 10.20.0.125 | vpn | 2 | 2 | 2026-09-15T01:14:24.000000Z | 2026-09-15T03:14:24.000000Z |

The full list is in [sources.csv](sources.csv). Counts cover the whole input; the queries below use shorter windows.

## Window matches

- [Repeated failures](failure_bursts.csv): 6 qualifying windows.
- [Failures across accounts](multiple_users.csv): 3 qualifying windows.
- [Success after failures](success_after_failures.csv): 1 matching success event(s).

Windows overlap. These row counts are not counts of separate incidents.

## Successful logins to review

| success_event_id | success_at | user | source_ip | preceding_failures |
| --- | --- | --- | --- | --- |
| EVT-01209 | 2026-09-15T14:08:00.000000Z | analyst_demo | 203.0.113.42 | 8 |

Start with the original event IDs, then check MFA, device details and user context. Those fields are absent from this sample.

[Sample notes](../docs/notes.md) · [SQL queries](../sql/) · [All results](results.json)
