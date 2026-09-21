SET search_path TO test_service, public;

CREATE TABLE executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_key VARCHAR(20) NOT NULL REFERENCES projects(project_key) ON DELETE RESTRICT,
  test_plan_id UUID NOT NULL REFERENCES test_plans(id) ON DELETE RESTRICT,
  environment_id UUID NOT NULL REFERENCES environments(id) ON DELETE RESTRICT,
  runner_version VARCHAR(100),
  trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('MANUAL', 'API', 'CI', 'SCHEDULE')),
  triggered_by VARCHAR(255),
  status VARCHAR(30) NOT NULL DEFAULT 'CREATED'
    CHECK (status IN ('CREATED', 'RUNNING', 'PASSED', 'FAILED', 'PARTIALLY_FAILED', 'CANCELLED', 'ERROR')),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  duration_ms BIGINT CHECK (duration_ms IS NULL OR duration_ms >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at)
);
