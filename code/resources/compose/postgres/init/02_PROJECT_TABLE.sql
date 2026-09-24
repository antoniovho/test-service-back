-- Creates the project table (Project Catalog entry scoping all test artifacts)

CREATE TABLE IF NOT EXISTS test_service_v1.project (
    key        TEXT            NOT NULL,
    name       TEXT            NOT NULL,
    status     TEXT            NOT NULL DEFAULT 'ACTIVE',
    created_at timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by TEXT            NOT NULL,
    deleted_at timestamptz(6)  NULL,
    deleted_by TEXT            NULL,
    CONSTRAINT project_pkey PRIMARY KEY (key)
);

COMMENT ON COLUMN test_service_v1.project.key        IS 'Stable key used to identify the project in the Project Catalog';
COMMENT ON COLUMN test_service_v1.project.name       IS 'Human-readable project name managed by Test Service';
COMMENT ON COLUMN test_service_v1.project.status     IS 'Project lifecycle status: ACTIVE or DELETED (logical deletion)';
COMMENT ON COLUMN test_service_v1.project.created_at IS 'Timestamp when the project was created';
COMMENT ON COLUMN test_service_v1.project.created_by IS 'Authenticated administrator that created the project';
COMMENT ON COLUMN test_service_v1.project.deleted_at IS 'Timestamp when the project was logically deleted; NULL while ACTIVE';
COMMENT ON COLUMN test_service_v1.project.deleted_by IS 'Authenticated administrator that logically deleted the project; NULL while ACTIVE';

CREATE INDEX IF NOT EXISTS idx_project_status ON test_service_v1.project (status);
