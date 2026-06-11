USE fmwchecks;

-- Add server columns to fmw_connection_result
ALTER TABLE fmw_connection_result
  ADD COLUMN server_host   VARCHAR(255) NOT NULL DEFAULT '' AFTER env_type,
  ADD COLUMN server_status VARCHAR(20)  NOT NULL DEFAULT 'NOT CONNECTED' AFTER server_host,
  ADD COLUMN server_error  TEXT         NULL AFTER server_status;

-- Rename total_dbs to total_envs in fmw_run
ALTER TABLE fmw_run
  CHANGE COLUMN total_dbs total_envs INT NOT NULL DEFAULT 0;

-- Add step_no, customer, env_type to fmw_run_log
ALTER TABLE fmw_run_log
  ADD COLUMN step_no   INT          NOT NULL DEFAULT 0 AFTER run_id,
  ADD COLUMN customer  VARCHAR(255) NULL AFTER message,
  ADD COLUMN env_type  VARCHAR(50)  NULL AFTER customer;

-- Add config_customers and config_envs to fmw_config
INSERT INTO fmw_config (config_key, config_value, description) VALUES
  ('config_customers', '', 'Comma-sep customer names; empty = ALL'),
  ('config_envs',      '', 'Comma-sep envs DEV,VAL,PRD; empty = ALL')
ON DUPLICATE KEY UPDATE description = VALUES(description);
