-- Creates the test_set table (immutable versions of composed test sets)

CREATE TABLE IF NOT EXISTS test_service_v1.test_set (
    id          uuid            DEFAULT gen_random_uuid() NOT NULL,
    project_key TEXT            NOT NULL,
    set_key     TEXT            NOT NULL,
    version     INTEGER         NOT NULL,
    name        TEXT            NOT NULL,
    description TEXT            NULL,
    status      TEXT            NOT NULL DEFAULT 'DRAFT',
    created_at  timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by  TEXT            NOT NULL,
    CONSTRAINT test_set_pkey PRIMARY KEY (id),
    CONSTRAINT test_set_key_version_uq UNIQUE (set_key, version)
);

COMMENT ON COLUMN test_service_v1.test_set.id          IS 'Unique immutable test set version identifier';
COMMENT ON COLUMN test_service_v1.test_set.project_key IS 'Project that owns this test set';
COMMENT ON COLUMN test_service_v1.test_set.set_key     IS 'Stable business key of the test set, shared across versions';
COMMENT ON COLUMN test_service_v1.test_set.version     IS 'Monotonically increasing version number for the set key';
COMMENT ON COLUMN test_service_v1.test_set.name        IS 'Human-readable test set name';
COMMENT ON COLUMN test_service_v1.test_set.description IS 'Purpose of the test set; nullable';
COMMENT ON COLUMN test_service_v1.test_set.status      IS 'Lifecycle status of this version: DRAFT, ACTIVE, or DEPRECATED';
COMMENT ON COLUMN test_service_v1.test_set.created_at  IS 'Timestamp when this version was created';
COMMENT ON COLUMN test_service_v1.test_set.created_by  IS 'Identity that created this version';

CREATE INDEX IF NOT EXISTS idx_test_set_project_key ON test_service_v1.test_set (project_key);
CREATE INDEX IF NOT EXISTS idx_test_set_set_key     ON test_service_v1.test_set (set_key);
CREATE INDEX IF NOT EXISTS idx_test_set_status      ON test_service_v1.test_set (status);
