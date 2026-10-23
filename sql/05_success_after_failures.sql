SELECT s.event_id AS success_event_id, s.timestamp AS success_at,
       s.user, s.source_ip, s.service,
       COUNT(f.event_id) AS preceding_failures,
       MIN(f.timestamp) AS first_failure
FROM auth_events s JOIN auth_events f
  ON f.service = s.service AND f.source_ip = s.source_ip AND f.user = s.user
 AND f.outcome = 'failure'
 AND f.epoch >= s.epoch - 900 AND f.epoch < s.epoch
WHERE s.outcome = 'success'
GROUP BY s.event_id
HAVING COUNT(f.event_id) >= 5
ORDER BY s.epoch, s.event_id;
