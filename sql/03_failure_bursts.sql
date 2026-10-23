-- One row per qualifying failure event. Overlapping windows are NOT separate incidents.
SELECT e.event_id, e.timestamp, e.user, e.source_ip, e.service,
       COUNT(f.event_id) AS failures_in_window
FROM auth_events e JOIN auth_events f
  ON f.service = e.service AND f.source_ip = e.source_ip AND f.user = e.user
 AND f.outcome = 'failure'
 AND f.epoch BETWEEN e.epoch - 600 AND e.epoch
WHERE e.outcome = 'failure'
GROUP BY e.event_id
HAVING COUNT(f.event_id) >= 5
ORDER BY e.epoch, e.event_id;
