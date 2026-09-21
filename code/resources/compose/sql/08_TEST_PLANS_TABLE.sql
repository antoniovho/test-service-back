SET search_path TO test_service, public;

CREATE TABLE test_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_key VARCHAR(20) NOT NULL REFERENCES projects(project_key) ON DELETE RESTRICT,
  plan_key VARCHAR(100) NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
    CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED')),
  execution_mode VARCHAR(20) NOT NULL,
  max_parallelism INTEGER,
  timeout_seconds INTEGER NOT NULL CHECK (timeout_seconds > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255) NOT NULL,
  metadata JSONB,
  UNIQUE (project_key, plan_key, version),
  CHECK (
    (execution_mode = 'SEQUENTIAL' AND max_parallelism IS NULL) OR
    (execution_mode = 'PARALLEL' AND max_parallelism IS NOT NULL AND max_parallelism > 0)
  )
);

CREATE UNIQUE INDEX uq_test_plans_one_active
  ON test_plans(project_key, plan_key)
  WHERE status = 'ACTIVE';
