-- Adds immutable per-entity Viewer publication history to existing databases.

CREATE TABLE IF NOT EXISTS test_service_v1.viewer_operation_item (
    id                   uuid           DEFAULT gen_random_uuid() NOT NULL,
    operation_id         uuid           NOT NULL,
    sync_record_id       uuid           NOT NULL,
    project_key          TEXT           NOT NULL,
    entity_type          TEXT           NOT NULL,
    entity_key           TEXT           NOT NULL,
    entity_version       integer        NOT NULL,
    projected_version_id uuid           NOT NULL,
    viewer_type          TEXT           NOT NULL,
    external_entity_key  TEXT           NOT NULL,
    external_entity_id   TEXT           NULL,
    sync_status          TEXT           NOT NULL,
    error                TEXT           NULL,
    created_at           timestamptz(6) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT viewer_operation_item_pkey PRIMARY KEY (id),
    CONSTRAINT viewer_operation_item_entity_version_chk CHECK (entity_version >= 1),
    CONSTRAINT viewer_operation_item_sync_status_chk CHECK (sync_status IN ('PENDING', 'SYNCED', 'ERROR', 'DRIFT_DETECTED'))
);

CREATE INDEX IF NOT EXISTS idx_viewer_operation_item_operation
    ON test_service_v1.viewer_operation_item (operation_id, created_at);

ALTER TABLE test_service_v1.viewer_operation_item
    ADD CONSTRAINT fk_viewer_operation_item_operation
    FOREIGN KEY (operation_id)
    REFERENCES test_service_v1.viewer_operation(id)
    ON DELETE CASCADE;

ALTER TABLE test_service_v1.viewer_operation_item
    ADD CONSTRAINT fk_viewer_operation_item_sync_record
    FOREIGN KEY (sync_record_id)
    REFERENCES test_service_v1.viewer_sync_record(id)
    ON DELETE RESTRICT;
