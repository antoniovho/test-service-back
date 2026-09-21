SET search_path TO test_service, public;

CREATE TABLE test_preconditions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_key VARCHAR(20) NOT NULL REFERENCES projects(project_key) ON DELETE RESTRICT,
  precondition_key VARCHAR(100) NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  name VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  validation_definition JSONB NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
    CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255) NOT NULL,
  metadata JSONB,
  UNIQUE (project_key, precondition_key, version)
);

CREATE UNIQUE INDEX uq_preconditions_one_active
  ON test_preconditions(project_key, precondition_key)
  WHERE status = 'ACTIVE';
