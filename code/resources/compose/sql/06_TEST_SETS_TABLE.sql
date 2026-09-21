SET search_path TO test_service, public;

CREATE TABLE test_sets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_key VARCHAR(20) NOT NULL REFERENCES projects(project_key) ON DELETE RESTRICT,
  set_key VARCHAR(100) NOT NULL,
  version INTEGER NOT NULL CHECK (version > 0),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
    CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255) NOT NULL,
  metadata JSONB,
  UNIQUE (project_key, set_key, version)
);

CREATE UNIQUE INDEX uq_test_sets_one_active
  ON test_sets(project_key, set_key)
  WHERE status = 'ACTIVE';
