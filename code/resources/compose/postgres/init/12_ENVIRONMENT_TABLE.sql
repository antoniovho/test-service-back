-- Creates the environment table (target environment configuration for executions)

CREATE TABLE IF NOT EXISTS test_service_v1.environment (
    id              uuid            DEFAULT gen_random_uuid() NOT NULL,
    environment_key TEXT            NOT NULL,
    name            TEXT            NOT NULL,
    description     TEXT            NULL,
    status          TEXT            NOT NULL DEFAULT 'ACTIVE',
    configuration   JSONB           NOT NULL DEFAULT '{}',
    created_at      timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by      TEXT            NOT NULL,
    CONSTRAINT environment_pkey PRIMARY KEY (id),
    CONSTRAINT environment_key_uq UNIQUE (environment_key)
);

COMMENT ON COLUMN test_service_v1.environment.id              IS 'Unique environment identifier';
COMMENT ON COLUMN test_service_v1.environment.environment_key IS 'Stable business key of the environment';
COMMENT ON COLUMN test_service_v1.environment.name            IS 'Human-readable environment name';
COMMENT ON COLUMN test_service_v1.environment.description     IS 'Purpose of the environment; nullable';
COMMENT ON COLUMN test_service_v1.environment.status          IS 'Lifecycle status of the environment: ACTIVE, INACTIVE, or DEPRECATED';
COMMENT ON COLUMN test_service_v1.environment.configuration   IS 'Environment-specific runtime configuration';
COMMENT ON COLUMN test_service_v1.environment.created_at      IS 'Timestamp when the environment was created';
COMMENT ON COLUMN test_service_v1.environment.created_by      IS 'Identity that created the environment';

CREATE INDEX IF NOT EXISTS idx_environment_status ON test_service_v1.environment (status);
