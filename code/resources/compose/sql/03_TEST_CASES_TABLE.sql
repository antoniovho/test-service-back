SET search_path TO test_service, public;

CREATE TABLE test_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_key VARCHAR(20) NOT NULL REFERENCES projects(project_key) ON DELETE RESTRICT,
  test_key VARCHAR(100) NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  name VARCHAR(255) NOT NULL,
  summary TEXT NOT NULL,
  objective TEXT NOT NULL CHECK (length(trim(objective)) > 0),
  test_type VARCHAR(30) NOT NULL CHECK (test_type IN ('AUTOMATED', 'MANUAL')),
  test_level VARCHAR(30) NOT NULL CHECK (
    test_level IN ('FUNCTIONAL', 'ERROR', 'INTEGRATION', 'PERFORMANCE', 'SECURITY', 'STRESS')
  ),
  priority VARCHAR(20) NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
    CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED')),
  schema_version VARCHAR(20) NOT NULL,
  definition JSONB NOT NULL,
  timeout_seconds INTEGER NOT NULL CHECK (timeout_seconds > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255) NOT NULL,
  metadata JSONB,
  UNIQUE (project_key, test_key, version)
);

CREATE UNIQUE INDEX uq_test_cases_one_active
  ON test_cases(project_key, test_key)
  WHERE status = 'ACTIVE';
