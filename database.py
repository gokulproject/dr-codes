DS-HC-05 — Rerun Screen:
Spec
Detail
DS-HC-05-01 Fields
Lists all rerun queue entries per customer and environment, showing original Run ID, rerun attempt number, maximum attempts allowed, current status (PENDING / IN_PROGRESS / COMPLETED / FAILED), scheduled fire time (IST), actual start time (IST), completed time (IST), and last error message if failed.

DS-HC-05-02 Validation
Maximum attempts must be a positive integer greater than zero. Scheduled rerun time must be a valid datetime. A rerun entry cannot be created if the original run ID does not exist in execution_runs. Duplicate rerun entries for the same run ID and attempt number are not permitted.

DS-HC-05-03 Navigation
A View button opens the original run report for that rerun entry. A Cancel button allows admin to cancel a PENDING rerun before it fires. Status badge updates automatically on the dashboard without a full page reload. Completed and Failed entries are retained in the list for audit purposes and are not auto-deleted.

DS-HC-05-04 Rerun Execution Behavior
When a rerun entry reaches PENDING status and its scheduled_at time has passed, the background poller (running every 60 seconds) picks it up and executes it automatically. If the rerun completes successfully the entry is marked COMPLETED and no further retries are attempted. If it fails again and attempts remaining, a new PENDING entry is created for the next attempt. If all attempts are exhausted without success, the entry is marked FAILED and a Rerun Exhausted alert email is sent to configured recipients
.
DS-HC-05-05 Suppression Behavior
If a manual run or scheduled run completes successfully for the same customer and environment while a rerun is still PENDING, the PENDING rerun entry is automatically cancelled and marked SKIPPED to avoid redundant execution.

DS-HC-05-06 Access Rules
App users can only view the rerun screen and rerun history. They are not permitted to cancel or manually trigger rerun entries. Only administrators have access to cancel PENDING reruns or adjust maximum attempt configuration per customer.