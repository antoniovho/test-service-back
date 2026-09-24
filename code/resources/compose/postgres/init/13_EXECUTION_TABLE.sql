-- Creates the execution table (execution instances created from a test plan and environment)

CREATE TABLE IF NOT EXISTS test_service_v1.execution (
    id              uuid            DEFAULT gen_random_uuid() NOT NULL,
    project_key     TEXT            NOT NULL,
    test_plan_id    uuid            NOT NULL,
    environment_id  uuid            NOT NULL,
    trigger_type    TEXT            NOT NULL,
    triggered_by    TEXT            NULL,
    status          TEXT            NOT NULL DEFAULT 'CREATED',
    runner_version  TEXT            NULL,
    started_at      timestamptz(6)  NULL,
    finished_at     timestamptz(6)  NULL,
    duration_ms     INTEGER         NULL,
    created_at      timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT execution_pkey PRIMARY KEY (id)
);

COMMENT ON COLUMN test_service_v1.execution.id             IS 'Unique execution identifier';
COMMENT ON COLUMN test_service_v1.execution.project_key    IS 'Project that owns this execution';
COMMENT ON COLUMN test_service_v1.execution.test_plan_id   IS 'UUID of the immutable test plan version executed';
COMMENT ON COLUMN test_service_v1.execution.environment_id IS 'UUID of the environment used for this execution';
COMMENT ON COLUMN test_service_v1.execution.trigger_type   IS 'Source that started the execution: MANUAL, API, CI, or SCHEDULE';
COMMENT ON COLUMN test_service_v1.execution.triggered_by   IS 'Identity or system that started the execution; nullable';
COMMENT ON COLUMN test_service_v1.execution.status         IS 'Current execution status';
COMMENT ON COLUMN test_service_v1.execution.runner_version IS 'Version of the execution runner; nullable';
COMMENT ON COLUMN test_service_v1.execution.started_at     IS 'Execution start timestamp; NULL until RUNNING';
COMMENT ON COLUMN test_service_v1.execution.finished_at    IS 'Execution completion timestamp; NULL until finished';
COMMENT ON COLUMN test_service_v1.execution.duration_ms    IS 'Execution duration in milliseconds; NULL until finished';
COMMENT ON COLUMN test_service_v1.execution.created_at     IS 'Timestamp when the execution record was created';

CREATE INDEX IF NOT EXISTS idx_execution_project_key    ON test_service_v1.execution (project_key);
CREATE INDEX IF NOT EXISTS idx_execution_test_plan_id   ON test_service_v1.execution (test_plan_id);
CREATE INDEX IF NOT EXISTS idx_execution_environment_id ON test_service_v1.execution (environment_id);
CREATE INDEX IF NOT EXISTS idx_execution_status         ON test_service_v1.execution (status);
