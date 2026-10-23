SELECT service, COUNT(*) AS events,
       SUM(outcome = 'success') AS successes,
       SUM(outcome = 'failure') AS failures,
       ROUND(100.0 * SUM(outcome = 'failure') / COUNT(*), 2) AS failure_pct,
       COUNT(DISTINCT user) AS users,
       COUNT(DISTINCT source_ip) AS sources
FROM auth_events
GROUP BY service ORDER BY events DESC, service;
