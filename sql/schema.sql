CREATE TABLE auth_events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    epoch REAL NOT NULL,
    user TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('success', 'failure')),
    service TEXT NOT NULL
);
CREATE INDEX identity_time ON auth_events(service, source_ip, user, epoch);
CREATE INDEX source_time ON auth_events(service, source_ip, epoch);
