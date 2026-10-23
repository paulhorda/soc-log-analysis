-- Count distinct accounts, not failed attempts against the same account.
SELECT e.event_id, e.timestamp, e.source_ip, e.service,
       COUNT(DISTINCT f.user) AS users_in_window,
       COUNT(f.event_id) AS failures_in_window
FROM auth_events e JOIN auth_events f
  ON f.service = e.service AND f.source_ip = e.source_ip
 AND f.outcome = 'failure'
 AND f.epoch BETWEEN e.epoch - 600 AND e.epoch
WHERE e.outcome = 'failure'
GROUP BY e.event_id
HAVING COUNT(DISTINCT f.user) >= 6
ORDER BY e.epoch, e.event_id;
