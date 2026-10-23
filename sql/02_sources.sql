-- Descriptive counts over the whole input, not a source-risk score.
SELECT source_ip, service, COUNT(*) AS failures,
       COUNT(DISTINCT user) AS affected_users,
       MIN(timestamp) AS first_failure, MAX(timestamp) AS last_failure
FROM auth_events WHERE outcome = 'failure'
GROUP BY source_ip, service
ORDER BY failures DESC, affected_users DESC, source_ip, service;
