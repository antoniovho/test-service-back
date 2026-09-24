-- Creates the test_plan_test_set table (test set versions included in a test plan version)

CREATE TABLE IF NOT EXISTS test_service_v1.test_plan_test_set (
    test_plan_id uuid NOT NULL,
    test_set_id  uuid NOT NULL,
    CONSTRAINT test_plan_test_set_pkey PRIMARY KEY (test_plan_id, test_set_id)
);

COMMENT ON COLUMN test_service_v1.test_plan_test_set.test_plan_id IS 'UUID of the test plan version that includes the test set';
COMMENT ON COLUMN test_service_v1.test_plan_test_set.test_set_id  IS 'UUID of the immutable test set version included in the plan';

CREATE INDEX IF NOT EXISTS idx_test_plan_test_set_test_set_id ON test_service_v1.test_plan_test_set (test_set_id);
