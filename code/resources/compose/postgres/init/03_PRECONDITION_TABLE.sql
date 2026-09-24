-- Creates the precondition table (immutable versions of validation preconditions)

CREATE TABLE IF NOT EXISTS test_service_v1.precondition (
    id                    uuid            DEFAULT gen_random_uuid() NOT NULL,
    project_key           TEXT            NOT NULL,
    precondition_key      TEXT            NOT NULL,
    version               INTEGER         NOT NULL,
    name                  TEXT            NOT NULL,
    description           TEXT            NOT NULL,
    validation_definition JSONB           NOT NULL,
    status                TEXT            NOT NULL DEFAULT 'DRAFT',
    metadata              JSONB           NOT NULL DEFAULT '{}',
    created_at            timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by            TEXT            NOT NULL,
    CONSTRAINT precondition_pkey PRIMARY KEY (id),
    CONSTRAINT precondition_key_version_uq UNIQUE (precondition_key, version)
);

COMMENT ON COLUMN test_service_v1.precondition.id                    IS 'Unique immutable precondition version identifier';
COMMENT ON COLUMN test_service_v1.precondition.project_key           IS 'Project that owns this precondition';
COMMENT ON COLUMN test_service_v1.precondition.precondition_key      IS 'Stable business key of the precondition, shared across versions';
COMMENT ON COLUMN test_service_v1.precondition.version               IS 'Monotonically increasing version number for the precondition key';
COMMENT ON COLUMN test_service_v1.precondition.name                  IS 'Human-readable precondition name';
COMMENT ON COLUMN test_service_v1.precondition.description           IS 'Behavior validated before execution';
COMMENT ON COLUMN test_service_v1.precondition.validation_definition IS 'Executable definition (schemaVersion, variables, actions) evaluated by the runner';
COMMENT ON COLUMN test_service_v1.precondition.status                IS 'Lifecycle status of this version: DRAFT, ACTIVE, or DEPRECATED';
COMMENT ON COLUMN test_service_v1.precondition.metadata               IS 'Additional domain metadata';
COMMENT ON COLUMN test_service_v1.precondition.created_at            IS 'Timestamp when this version was created';
COMMENT ON COLUMN test_service_v1.precondition.created_by            IS 'Identity that created this version';

CREATE INDEX IF NOT EXISTS idx_precondition_project_key      ON test_service_v1.precondition (project_key);
CREATE INDEX IF NOT EXISTS idx_precondition_precondition_key ON test_service_v1.precondition (precondition_key);
CREATE INDEX IF NOT EXISTS idx_precondition_status           ON test_service_v1.precondition (status);
