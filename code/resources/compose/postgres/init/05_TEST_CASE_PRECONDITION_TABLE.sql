-- Creates the test_case_precondition table (ordered preconditions required by a test case version)

CREATE TABLE IF NOT EXISTS test_service_v1.test_case_precondition (
    id              uuid    DEFAULT gen_random_uuid() NOT NULL,
    test_case_id    uuid    NOT NULL,
    precondition_id uuid    NOT NULL,
    position        INTEGER NOT NULL,
    CONSTRAINT test_case_precondition_pkey PRIMARY KEY (id),
    CONSTRAINT test_case_precondition_position_uq UNIQUE (test_case_id, position),
    CONSTRAINT test_case_precondition_test_case_precondition_uq
    UNIQUE (test_case_id, precondition_id)
);

COMMENT ON COLUMN test_service_v1.test_case_precondition.id              IS 'Unique row identifier';
COMMENT ON COLUMN test_service_v1.test_case_precondition.test_case_id    IS 'UUID of the test case version that requires the precondition';
COMMENT ON COLUMN test_service_v1.test_case_precondition.precondition_id IS 'UUID of the immutable precondition version required before execution';
COMMENT ON COLUMN test_service_v1.test_case_precondition.position        IS 'Zero-based evaluation order of the precondition within the test case';

CREATE INDEX IF NOT EXISTS idx_test_case_precondition_test_case_id    ON test_service_v1.test_case_precondition (test_case_id);
CREATE INDEX IF NOT EXISTS idx_test_case_precondition_precondition_id ON test_service_v1.test_case_precondition (precondition_id);
