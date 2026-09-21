SET search_path TO test_service, public;

CREATE TABLE test_plan_test_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_plan_id UUID NOT NULL REFERENCES test_plans(id) ON DELETE RESTRICT,
  test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE RESTRICT,
  sequence INTEGER NOT NULL CHECK (sequence > 0),
  UNIQUE (test_plan_id, test_case_id),
  UNIQUE (test_plan_id, sequence)
);
