-- Creates the test_result_artifact table (artifacts generated while executing a test result)

CREATE TABLE IF NOT EXISTS test_service_v1.test_result_artifact (
    id               uuid            DEFAULT gen_random_uuid() NOT NULL,
    test_result_id   uuid            NOT NULL,
    action_result_id uuid            NULL,
    artifact_type    TEXT            NOT NULL,
    storage_type     TEXT            NOT NULL,
    storage_uri      TEXT            NULL,
    content_hash     TEXT            NULL,
    size_bytes       INTEGER         NULL,
    mime_type        TEXT            NULL,
    created_at       timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT test_result_artifact_pkey PRIMARY KEY (id)
);

COMMENT ON COLUMN test_service_v1.test_result_artifact.id               IS 'Unique artifact identifier';
COMMENT ON COLUMN test_service_v1.test_result_artifact.test_result_id   IS 'UUID of the test result that this artifact belongs to';
COMMENT ON COLUMN test_service_v1.test_result_artifact.action_result_id IS 'UUID of the action result associated with the artifact, when applicable; nullable';
COMMENT ON COLUMN test_service_v1.test_result_artifact.artifact_type    IS 'Kind of generated artifact: REQUEST, RESPONSE, SSE_TRACE, LOG, or OTHER';
COMMENT ON COLUMN test_service_v1.test_result_artifact.storage_type     IS 'Storage backend containing the artifact: DB or OBJECT_STORAGE';
COMMENT ON COLUMN test_service_v1.test_result_artifact.storage_uri      IS 'URI used to retrieve the artifact; nullable';
COMMENT ON COLUMN test_service_v1.test_result_artifact.content_hash     IS 'Hash of the artifact content; nullable';
COMMENT ON COLUMN test_service_v1.test_result_artifact.size_bytes       IS 'Artifact size in bytes; nullable';
COMMENT ON COLUMN test_service_v1.test_result_artifact.mime_type        IS 'Artifact media type; nullable';
COMMENT ON COLUMN test_service_v1.test_result_artifact.created_at       IS 'Timestamp when the artifact record was created';

CREATE INDEX IF NOT EXISTS idx_test_result_artifact_test_result_id   ON test_service_v1.test_result_artifact (test_result_id);
CREATE INDEX IF NOT EXISTS idx_test_result_artifact_action_result_id ON test_service_v1.test_result_artifact (action_result_id);
