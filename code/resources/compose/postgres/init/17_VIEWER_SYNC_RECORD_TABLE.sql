-- Creates the viewer_sync_record table (synchronization state between a domain entity and its external viewer projection)

CREATE TABLE IF NOT EXISTS test_service_v1.viewer_sync_record (
    id                    uuid            DEFAULT gen_random_uuid() NOT NULL,
    entity_type           TEXT            NOT NULL,
    entity_key            TEXT            NOT NULL,
    projected_version_id  uuid            NOT NULL,
    viewer_type           TEXT            NOT NULL,
    external_entity_key   TEXT            NOT NULL,
    external_entity_id    TEXT            NULL,
    sync_status           TEXT            NOT NULL DEFAULT 'PENDING',
    last_synced_at        timestamptz(6)  NULL,
    last_checked_at       timestamptz(6)  NULL,
    created_at            timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT viewer_sync_record_pkey PRIMARY KEY (id),
    CONSTRAINT viewer_sync_record_entity_viewer_uq UNIQUE (entity_type, entity_key, viewer_type)
);

COMMENT ON COLUMN test_service_v1.viewer_sync_record.id                   IS 'Unique synchronization record identifier';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.entity_type          IS 'Type of domain entity represented in the external viewer: TEST_CASE, PRECONDITION, TEST_SET, or TEST_PLAN';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.entity_key           IS 'Stable business key of the logical domain entity, unchanged across versions';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.projected_version_id IS 'UUID of the immutable domain version currently projected to the external viewer';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.viewer_type          IS 'Type of external viewer containing the projection, e.g. XRAY';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.external_entity_key  IS 'Stable identifier of the projected entity in the external viewer';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.external_entity_id   IS 'Optional technical identifier assigned by the external viewer; nullable';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.sync_status          IS 'Current synchronization status: PENDING, SYNCED, ERROR, or DRIFT_DETECTED';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.last_synced_at       IS 'Last successful synchronization timestamp; nullable';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.last_checked_at      IS 'Last drift check timestamp; nullable';
COMMENT ON COLUMN test_service_v1.viewer_sync_record.created_at           IS 'Timestamp when the projection record was created';

CREATE INDEX IF NOT EXISTS idx_viewer_sync_record_entity_key  ON test_service_v1.viewer_sync_record (entity_key);
CREATE INDEX IF NOT EXISTS idx_viewer_sync_record_sync_status ON test_service_v1.viewer_sync_record (sync_status);
