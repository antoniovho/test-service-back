SET search_path TO test_service, public;

CREATE TABLE test_plan_exclusions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_plan_id UUID NOT NULL REFERENCES test_plans(id) ON DELETE RESTRICT,
  test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE RESTRICT,
  reason TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255) NOT NULL,
  UNIQUE (test_plan_id, test_case_id)
);
