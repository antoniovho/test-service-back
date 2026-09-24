-- Creates the test_case table (immutable versions of authored test cases)

CREATE TABLE IF NOT EXISTS test_service_v1.test_case (
    id              uuid            DEFAULT gen_random_uuid() NOT NULL,
    project_key     TEXT            NOT NULL,
    test_key        TEXT            NOT NULL,
    version         INTEGER         NOT NULL,
    name            TEXT            NOT NULL,
    summary         TEXT            NOT NULL,
    objective       TEXT            NOT NULL,
    test_type       TEXT            NOT NULL,
    test_level      TEXT            NOT NULL,
    priority        TEXT            NOT NULL,
    status          TEXT            NOT NULL DEFAULT 'DRAFT',
    definition      JSONB           NOT NULL,
    timeout_seconds INTEGER         NOT NULL,
    metadata        JSONB           NOT NULL DEFAULT '{}',
    created_at      timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by      TEXT            NOT NULL,
    CONSTRAINT test_case_pkey PRIMARY KEY (id),
    CONSTRAINT test_case_key_version_uq UNIQUE (test_key, version)
);

COMMENT ON COLUMN test_service_v1.test_case.id              IS 'Unique immutable test case version identifier';
COMMENT ON COLUMN test_service_v1.test_case.project_key     IS 'Project that owns this test case';
COMMENT ON COLUMN test_service_v1.test_case.test_key        IS 'Stable business key of the test case, shared across versions';
COMMENT ON COLUMN test_service_v1.test_case.version         IS 'Monotonically increasing version number for the test key';
COMMENT ON COLUMN test_service_v1.test_case.name            IS 'Human-readable test case name';
COMMENT ON COLUMN test_service_v1.test_case.summary         IS 'Short summary of the scenario';
COMMENT ON COLUMN test_service_v1.test_case.objective       IS 'Expected objective of the test';
COMMENT ON COLUMN test_service_v1.test_case.test_type       IS 'Test execution modality: AUTOMATED or MANUAL';
COMMENT ON COLUMN test_service_v1.test_case.test_level      IS 'Test level in the quality model: FUNCTIONAL, ERROR, INTEGRATION, PERFORMANCE, SECURITY, or STRESS';
COMMENT ON COLUMN test_service_v1.test_case.priority        IS 'Business priority of the test: LOW, MEDIUM, HIGH, or CRITICAL';
COMMENT ON COLUMN test_service_v1.test_case.status          IS 'Lifecycle status of this version: DRAFT, ACTIVE, or DEPRECATED';
COMMENT ON COLUMN test_service_v1.test_case.definition      IS 'Executable definition (schemaVersion, variables, actions) evaluated by the runner';
COMMENT ON COLUMN test_service_v1.test_case.timeout_seconds IS 'Maximum execution time in seconds';
COMMENT ON COLUMN test_service_v1.test_case.metadata        IS 'Additional domain metadata';
COMMENT ON COLUMN test_service_v1.test_case.created_at      IS 'Timestamp when this version was created';
COMMENT ON COLUMN test_service_v1.test_case.created_by      IS 'Identity that created this version';

CREATE INDEX IF NOT EXISTS idx_test_case_project_key ON test_service_v1.test_case (project_key);
CREATE INDEX IF NOT EXISTS idx_test_case_test_key    ON test_service_v1.test_case (test_key);
CREATE INDEX IF NOT EXISTS idx_test_case_status      ON test_service_v1.test_case (status);
