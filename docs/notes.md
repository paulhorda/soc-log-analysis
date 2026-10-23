# Notes on the sample

All records are generated locally. `scenario_labels.json` describes the intended cases and is not used by the queries.

- **203.0.113.42:** eight failures for `analyst_demo`, then a success. The success query should return `EVT-01209` with eight preceding failures.
- **198.51.100.23:** failures against eight different accounts. The distinct-user threshold is reached at the sixth account.
- **10.20.0.250:** six failures from a fictional backup service with an outdated stored password. It matches the repeated-failure query. The benign explanation comes from the scenario, not from the log fields.
- **192.0.2.90:** eight accounts over 140 minutes. The overall source count stands out, but no ten-minute window reaches the distinct-user threshold.

## Why window counts differ from alert counts

The Python detector in the companion project applies a cooldown after the first alert. These SQL queries return all matches so the individual windows can be inspected. Several rows can refer to the same sequence of events.

Failure windows include both time boundaries. Success correlation excludes failures at exactly the same timestamp as the success: their order is unknown. Queries run after the full file is loaded, so failure windows include all events at their endpoint timestamp, regardless of line order.

## Working with other logs

The input is a normalized lab format. Real VPN, Windows or identity-provider logs need a separate field mapping. User and service names are case-sensitive. The loader reads the entire file into memory. SQL indexes support these joins, but this has not been tested as a large-scale log platform.

MFA, source ownership, device identity and activity after login are needed to reach a case disposition. A high failure count alone is insufficient.
