-- Creates the test_plan_test_case table (individual test case versions included in a test plan version)

CREATE TABLE IF NOT EXISTS test_service_v1.test_plan_test_case (
    test_plan_id uuid NOT NULL,
    test_case_id uuid NOT NULL,
    CONSTRAINT test_plan_test_case_pkey PRIMARY KEY (test_plan_id, test_case_id)
);

COMMENT ON COLUMN test_service_v1.test_plan_test_case.test_plan_id IS 'UUID of the test plan version that includes the test case';
COMMENT ON COLUMN test_service_v1.test_plan_test_case.test_case_id IS 'UUID of the immutable test case version included in the plan';

CREATE INDEX IF NOT EXISTS idx_test_plan_test_case_test_case_id ON test_service_v1.test_plan_test_case (test_case_id);
