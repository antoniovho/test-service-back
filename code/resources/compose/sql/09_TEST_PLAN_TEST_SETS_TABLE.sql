SET search_path TO test_service, public;

CREATE TABLE test_plan_test_sets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_plan_id UUID NOT NULL REFERENCES test_plans(id) ON DELETE RESTRICT,
  test_set_id UUID NOT NULL REFERENCES test_sets(id) ON DELETE RESTRICT,
  sequence INTEGER NOT NULL CHECK (sequence > 0),
  UNIQUE (test_plan_id, test_set_id),
  UNIQUE (test_plan_id, sequence)
);
