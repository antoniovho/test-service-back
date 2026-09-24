-- Creates the test_plan table (immutable versions of executable test plans)

CREATE TABLE IF NOT EXISTS test_service_v1.test_plan (
    id              uuid            DEFAULT gen_random_uuid() NOT NULL,
    project_key     TEXT            NOT NULL,
    plan_key        TEXT            NOT NULL,
    version         INTEGER         NOT NULL,
    name            TEXT            NOT NULL,
    description     TEXT            NULL,
    status          TEXT            NOT NULL DEFAULT 'DRAFT',
    execution_mode  TEXT            NOT NULL,
    max_parallelism INTEGER         NULL,
    timeout_seconds INTEGER         NOT NULL,
    created_at      timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by      TEXT            NOT NULL,
    CONSTRAINT test_plan_pkey PRIMARY KEY (id),
    CONSTRAINT test_plan_key_version_uq UNIQUE (plan_key, version)
);

COMMENT ON COLUMN test_service_v1.test_plan.id              IS 'Unique immutable test plan version identifier';
COMMENT ON COLUMN test_service_v1.test_plan.project_key     IS 'Project that owns this test plan';
COMMENT ON COLUMN test_service_v1.test_plan.plan_key        IS 'Stable business key of the test plan, shared across versions';
COMMENT ON COLUMN test_service_v1.test_plan.version         IS 'Monotonically increasing version number for the plan key';
COMMENT ON COLUMN test_service_v1.test_plan.name            IS 'Human-readable test plan name';
COMMENT ON COLUMN test_service_v1.test_plan.description     IS 'Purpose of the test plan; nullable';
COMMENT ON COLUMN test_service_v1.test_plan.status          IS 'Lifecycle status of this version: DRAFT, ACTIVE, or DEPRECATED';
COMMENT ON COLUMN test_service_v1.test_plan.execution_mode  IS 'Scheduling mode for plan items: SEQUENTIAL or PARALLEL';
COMMENT ON COLUMN test_service_v1.test_plan.max_parallelism IS 'Maximum number of concurrent executions; nullable';
COMMENT ON COLUMN test_service_v1.test_plan.timeout_seconds IS 'Maximum plan execution time in seconds';
COMMENT ON COLUMN test_service_v1.test_plan.created_at      IS 'Timestamp when this version was created';
COMMENT ON COLUMN test_service_v1.test_plan.created_by      IS 'Identity that created this version';

CREATE INDEX IF NOT EXISTS idx_test_plan_project_key ON test_service_v1.test_plan (project_key);
CREATE INDEX IF NOT EXISTS idx_test_plan_plan_key    ON test_service_v1.test_plan (plan_key);
CREATE INDEX IF NOT EXISTS idx_test_plan_status      ON test_service_v1.test_plan (status);
