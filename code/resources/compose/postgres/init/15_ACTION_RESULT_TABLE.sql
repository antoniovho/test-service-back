-- Creates the action_result table (result produced by executing one action of a test definition)

CREATE TABLE IF NOT EXISTS test_service_v1.action_result (
    id             uuid            DEFAULT gen_random_uuid() NOT NULL,
    test_result_id uuid            NOT NULL,
    action_id      TEXT            NOT NULL,
    action_type    TEXT            NOT NULL,
    status         TEXT            NOT NULL,
    started_at     timestamptz(6)  NULL,
    finished_at    timestamptz(6)  NULL,
    duration_ms    INTEGER         NULL,
    expected       JSONB           NULL,
    actual         JSONB           NULL,
    output         JSONB           NULL,
    error_code     TEXT            NULL,
    error_message  TEXT            NULL,
    created_at     timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT action_result_pkey PRIMARY KEY (id)
);

COMMENT ON COLUMN test_service_v1.action_result.id             IS 'Unique action result identifier';
COMMENT ON COLUMN test_service_v1.action_result.test_result_id IS 'UUID of the test result that this action belongs to';
COMMENT ON COLUMN test_service_v1.action_result.action_id      IS 'Identifier of the action in the executed test definition';
COMMENT ON COLUMN test_service_v1.action_result.action_type    IS 'Executed action type resolved by the Action Registry';
COMMENT ON COLUMN test_service_v1.action_result.status         IS 'Final status of the action execution';
COMMENT ON COLUMN test_service_v1.action_result.started_at     IS 'Action start timestamp; nullable';
COMMENT ON COLUMN test_service_v1.action_result.finished_at    IS 'Action completion timestamp; nullable';
COMMENT ON COLUMN test_service_v1.action_result.duration_ms    IS 'Action execution duration in milliseconds; nullable';
COMMENT ON COLUMN test_service_v1.action_result.expected       IS 'Expected result validated by the action; large payloads belong in test_result_artifact';
COMMENT ON COLUMN test_service_v1.action_result.actual         IS 'Actual structured result observed; large payloads belong in test_result_artifact';
COMMENT ON COLUMN test_service_v1.action_result.output         IS 'Structured values produced by the action; large payloads belong in test_result_artifact';
COMMENT ON COLUMN test_service_v1.action_result.error_code     IS 'Machine-readable action failure code; nullable';
COMMENT ON COLUMN test_service_v1.action_result.error_message  IS 'Human-readable action failure message; nullable';
COMMENT ON COLUMN test_service_v1.action_result.created_at     IS 'Timestamp when this action result record was created';

CREATE INDEX IF NOT EXISTS idx_action_result_test_result_id ON test_service_v1.action_result (test_result_id);
CREATE INDEX IF NOT EXISTS idx_action_result_status         ON test_service_v1.action_result (status);
