-- Creates the test_result table (immutable result produced by executing one test case)

CREATE TABLE IF NOT EXISTS test_service_v1.test_result (
    id            uuid            DEFAULT gen_random_uuid() NOT NULL,
    execution_id  uuid            NOT NULL,
    test_case_id  uuid            NOT NULL,
    status        TEXT            NOT NULL,
    started_at    timestamptz(6)  NULL,
    finished_at   timestamptz(6)  NULL,
    duration_ms   INTEGER         NULL,
    error_code    TEXT            NULL,
    error_message TEXT            NULL,
    created_at    timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT test_result_pkey PRIMARY KEY (id)
);

COMMENT ON COLUMN test_service_v1.test_result.id            IS 'Unique test result identifier';
COMMENT ON COLUMN test_service_v1.test_result.execution_id  IS 'UUID of the execution that produced this result';
COMMENT ON COLUMN test_service_v1.test_result.test_case_id  IS 'UUID of the immutable test case version executed';
COMMENT ON COLUMN test_service_v1.test_result.status        IS 'Final status of the test case execution';
COMMENT ON COLUMN test_service_v1.test_result.started_at    IS 'Test start timestamp; nullable';
COMMENT ON COLUMN test_service_v1.test_result.finished_at   IS 'Test completion timestamp; nullable';
COMMENT ON COLUMN test_service_v1.test_result.duration_ms   IS 'Test duration in milliseconds; nullable';
COMMENT ON COLUMN test_service_v1.test_result.error_code    IS 'Machine-readable failure code; nullable';
COMMENT ON COLUMN test_service_v1.test_result.error_message IS 'Human-readable failure message; nullable';
COMMENT ON COLUMN test_service_v1.test_result.created_at    IS 'Timestamp when this result record was created';

CREATE INDEX IF NOT EXISTS idx_test_result_execution_id ON test_service_v1.test_result (execution_id);
CREATE INDEX IF NOT EXISTS idx_test_result_test_case_id ON test_service_v1.test_result (test_case_id);
CREATE INDEX IF NOT EXISTS idx_test_result_status       ON test_service_v1.test_result (status);
