-- Adds immutable execution composition and runner evidence to existing databases.

ALTER TABLE test_service_v1.execution
    ADD COLUMN IF NOT EXISTS test_case_ids uuid[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS environment_snapshot JSONB NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS runner_identifier TEXT NULL;

COMMENT ON COLUMN test_service_v1.execution.test_case_ids IS 'Ordered effective Test Case snapshot UUIDs fixed at scheduling';
COMMENT ON COLUMN test_service_v1.execution.environment_snapshot IS 'Safe unresolved environment configuration fixed at scheduling';
COMMENT ON COLUMN test_service_v1.execution.runner_identifier IS 'Stable identifier of the accepted execution runner; nullable';
