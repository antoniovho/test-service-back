SET search_path TO test_service, public;

CREATE TABLE test_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE RESTRICT,
  test_case_id UUID NOT NULL REFERENCES test_cases(id) ON DELETE RESTRICT,
  status VARCHAR(20) NOT NULL CHECK (status IN ('PASSED', 'FAILED', 'ERROR', 'BLOCKED', 'SKIPPED')),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  duration_ms BIGINT CHECK (duration_ms IS NULL OR duration_ms >= 0),
  error_code VARCHAR(100),
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (execution_id, test_case_id),
  CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at)
);
