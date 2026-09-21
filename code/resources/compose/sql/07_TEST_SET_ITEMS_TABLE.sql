SET search_path TO test_service, public;

CREATE TABLE test_set_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_set_id UUID NOT NULL REFERENCES test_sets(id) ON DELETE RESTRICT,
  test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE RESTRICT,
  sequence INTEGER NOT NULL CHECK (sequence > 0),
  UNIQUE (test_set_id, test_case_id),
  UNIQUE (test_set_id, sequence)
);
