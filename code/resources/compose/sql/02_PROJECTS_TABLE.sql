SET search_path TO test_service, public;

CREATE TABLE projects (
  project_key VARCHAR(20) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
    CHECK (status IN ('ACTIVE', 'DELETED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255) NOT NULL,
  deleted_at TIMESTAMPTZ,
  deleted_by VARCHAR(255),
  CHECK (
    (status = 'ACTIVE' AND deleted_at IS NULL AND deleted_by IS NULL) OR
    (status = 'DELETED' AND deleted_at IS NOT NULL AND deleted_by IS NOT NULL)
  )
);
