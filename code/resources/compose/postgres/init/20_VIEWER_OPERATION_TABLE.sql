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

ALTER TABLE test_service_v1.viewer_sync_record
    ADD COLUMN IF NOT EXISTS operation_id uuid NULL;

CREATE INDEX IF NOT EXISTS idx_viewer_operation_pending
    ON test_service_v1.viewer_operation (created_at)
    WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_viewer_operation_project
    ON test_service_v1.viewer_operation (project_key, created_at);
CREATE INDEX IF NOT EXISTS idx_viewer_sync_record_operation
    ON test_service_v1.viewer_sync_record (operation_id);

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
END $$;
