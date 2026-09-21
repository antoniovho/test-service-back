SET search_path TO test_service, public;

CREATE TABLE action_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_result_id UUID NOT NULL REFERENCES test_results(id) ON DELETE RESTRICT,
  action_id VARCHAR(100) NOT NULL,
  action_type VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('PASSED', 'FAILED', 'ERROR', 'BLOCKED', 'SKIPPED')),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  duration_ms BIGINT CHECK (duration_ms IS NULL OR duration_ms >= 0),
  expected JSONB,
  actual JSONB,
  output JSONB,
  error_code VARCHAR(100),
  error_message TEXT,
  UNIQUE (test_result_id, action_id),
  CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at)
);
