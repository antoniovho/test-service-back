SET search_path TO test_service, public;

CREATE TABLE viewer_sync_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(30) NOT NULL
    CHECK (entity_type IN ('TEST_CASE', 'PRECONDITION', 'TEST_SET', 'TEST_PLAN')),
  entity_key VARCHAR(100) NOT NULL,
  projected_version_id UUID NOT NULL,
  viewer_type VARCHAR(30) NOT NULL CHECK (viewer_type IN ('XRAY')),
  external_entity_key VARCHAR(255) NOT NULL,
  external_entity_id VARCHAR(255),
  sync_status VARCHAR(30) NOT NULL DEFAULT 'PENDING'
    CHECK (sync_status IN ('PENDING', 'SYNCED', 'ERROR', 'DRIFT_DETECTED')),
  last_synced_at TIMESTAMPTZ,
  last_checked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (entity_type, entity_key),
  UNIQUE (viewer_type, external_entity_key)
);
