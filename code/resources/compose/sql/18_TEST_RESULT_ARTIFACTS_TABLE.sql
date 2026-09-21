SET search_path TO test_service, public;

CREATE TABLE test_result_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_result_id UUID NOT NULL REFERENCES test_results(id) ON DELETE RESTRICT,
  action_result_id UUID REFERENCES action_results(id) ON DELETE RESTRICT,
  artifact_type VARCHAR(30) NOT NULL CHECK (artifact_type IN ('REQUEST', 'RESPONSE', 'SSE_TRACE', 'LOG', 'OTHER')),
  storage_type VARCHAR(30) NOT NULL CHECK (storage_type IN ('DB', 'OBJECT_STORAGE')),
  storage_uri TEXT,
  content BYTEA,
  content_hash VARCHAR(128),
  size_bytes BIGINT CHECK (size_bytes IS NULL OR size_bytes >= 0),
  mime_type VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (
    (storage_type = 'DB' AND content IS NOT NULL AND storage_uri IS NULL) OR
    (storage_type = 'OBJECT_STORAGE' AND storage_uri IS NOT NULL AND content IS NULL)
  )
);
