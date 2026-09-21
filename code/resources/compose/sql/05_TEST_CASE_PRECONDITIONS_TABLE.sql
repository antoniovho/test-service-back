SET search_path TO test_service, public;

CREATE TABLE test_case_preconditions (
  test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE RESTRICT,
  precondition_id UUID NOT NULL REFERENCES test_preconditions(id) ON DELETE RESTRICT,
  sequence INTEGER NOT NULL CHECK (sequence > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255) NOT NULL,
  PRIMARY KEY (test_case_id, precondition_id),
  UNIQUE (test_case_id, sequence)
);
