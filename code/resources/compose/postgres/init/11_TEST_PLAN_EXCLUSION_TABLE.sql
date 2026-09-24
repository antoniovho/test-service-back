-- Creates the test_plan_exclusion table (test case versions excluded from plan execution)

CREATE TABLE IF NOT EXISTS test_service_v1.test_plan_exclusion (
    test_plan_id uuid NOT NULL,
    test_case_id uuid NOT NULL,
    CONSTRAINT test_plan_exclusion_pkey PRIMARY KEY (test_plan_id, test_case_id)
);

COMMENT ON COLUMN test_service_v1.test_plan_exclusion.test_plan_id IS 'UUID of the test plan version that excludes the test case';
COMMENT ON COLUMN test_service_v1.test_plan_exclusion.test_case_id IS 'UUID of the immutable test case version excluded from execution';

CREATE INDEX IF NOT EXISTS idx_test_plan_exclusion_test_case_id ON test_service_v1.test_plan_exclusion (test_case_id);
