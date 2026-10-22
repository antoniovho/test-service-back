-- Creates durable work records for publishing one execution to one external viewer.

CREATE TABLE IF NOT EXISTS test_service_v1.viewer_result_publication (
    id                     uuid           DEFAULT gen_random_uuid() NOT NULL,
    project_key            TEXT           NOT NULL,
    execution_id           uuid           NOT NULL,
    viewer_type            TEXT           NOT NULL,
    status                 TEXT           NOT NULL,
    attempts               INTEGER        NOT NULL DEFAULT 0,
    next_attempt_at        timestamptz(6) NULL,
    started_at             timestamptz(6) NULL,
    finished_at            timestamptz(6) NULL,
    external_execution_id  TEXT           NULL,
    external_execution_key TEXT           NULL,
    error                  TEXT           NULL,
    created_at             timestamptz(6) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at             timestamptz(6) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT viewer_result_publication_pkey PRIMARY KEY (id),
    CONSTRAINT uq_viewer_result_execution UNIQUE (execution_id, viewer_type),
    CONSTRAINT fk_viewer_result_publication_project
        FOREIGN KEY (project_key)
        REFERENCES test_service_v1.project(key)
        ON DELETE RESTRICT,
    CONSTRAINT fk_viewer_result_publication_execution
        FOREIGN KEY (execution_id)
        REFERENCES test_service_v1.execution(id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_viewer_result_publication_status
        CHECK (status IN ('PENDING', 'RUNNING', 'RETRY_WAIT', 'SUCCEEDED', 'FAILED_PERMANENT')),
    CONSTRAINT chk_viewer_result_publication_attempts CHECK (attempts >= 0)
);

CREATE INDEX IF NOT EXISTS ix_viewer_result_publication_due
    ON test_service_v1.viewer_result_publication (status, next_attempt_at, created_at);
