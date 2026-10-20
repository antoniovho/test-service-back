-- Creates durable, asynchronously processed Viewer operations.

CREATE TABLE IF NOT EXISTS test_service_v1.viewer_operation (
    id              uuid            DEFAULT gen_random_uuid() NOT NULL,
    project_key     TEXT            NOT NULL,
    viewer_type     TEXT            NOT NULL,
    operation_type  TEXT            NOT NULL,
    status          TEXT            NOT NULL DEFAULT 'PENDING',
    created_at      timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at      timestamptz(6)  NULL,
    finished_at     timestamptz(6)  NULL,
    total_items     integer         NULL,
    succeeded_items integer         NULL,
    failed_items    integer         NULL,
    error           TEXT            NULL,
    CONSTRAINT viewer_operation_pkey PRIMARY KEY (id),
    CONSTRAINT viewer_operation_status_chk CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'PARTIALLY_SUCCEEDED', 'FAILED')),
    CONSTRAINT viewer_operation_type_chk CHECK (operation_type IN ('PUBLICATION', 'DRIFT_CHECK'))
);

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

ALTER TABLE test_service_v1.viewer_sync_record
    ADD COLUMN IF NOT EXISTS operation_id uuid NULL;

CREATE INDEX IF NOT EXISTS idx_viewer_operation_pending
    ON test_service_v1.viewer_operation (created_at)
    WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_viewer_operation_project
    ON test_service_v1.viewer_operation (project_key, created_at);
CREATE INDEX IF NOT EXISTS idx_viewer_sync_record_operation
    ON test_service_v1.viewer_sync_record (operation_id);
CREATE INDEX IF NOT EXISTS idx_viewer_operation_item_operation
    ON test_service_v1.viewer_operation_item (operation_id, created_at);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_viewer_operation_project'
          AND table_name = 'viewer_operation'
    ) THEN
        ALTER TABLE test_service_v1.viewer_operation
            ADD CONSTRAINT fk_viewer_operation_project
            FOREIGN KEY (project_key)
            REFERENCES test_service_v1.project(key)
            ON DELETE RESTRICT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_viewer_sync_record_operation'
          AND table_name = 'viewer_sync_record'
    ) THEN
        ALTER TABLE test_service_v1.viewer_sync_record
            ADD CONSTRAINT fk_viewer_sync_record_operation
            FOREIGN KEY (operation_id)
            REFERENCES test_service_v1.viewer_operation(id)
            ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_viewer_operation_item_operation'
          AND table_name = 'viewer_operation_item'
    ) THEN
        ALTER TABLE test_service_v1.viewer_operation_item
            ADD CONSTRAINT fk_viewer_operation_item_operation
            FOREIGN KEY (operation_id)
            REFERENCES test_service_v1.viewer_operation(id)
            ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_viewer_operation_item_sync_record'
          AND table_name = 'viewer_operation_item'
    ) THEN
        ALTER TABLE test_service_v1.viewer_operation_item
            ADD CONSTRAINT fk_viewer_operation_item_sync_record
            FOREIGN KEY (sync_record_id)
            REFERENCES test_service_v1.viewer_sync_record(id)
            ON DELETE RESTRICT;
    END IF;
END $$;
