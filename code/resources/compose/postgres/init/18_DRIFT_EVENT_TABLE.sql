-- Creates the drift_event table (immutable record of a difference detected in the external viewer)

CREATE TABLE IF NOT EXISTS test_service_v1.drift_event (
    id                    uuid            DEFAULT gen_random_uuid() NOT NULL,
    sync_record_id        uuid            NOT NULL,
    projected_version_id  uuid            NOT NULL,
    detected_at           timestamptz(6)  NOT NULL,
    drift_type            TEXT            NOT NULL,
    notification_status   TEXT            NOT NULL DEFAULT 'PENDING',
    details               JSONB           NULL,
    created_at            timestamptz(6)  DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT drift_event_pkey PRIMARY KEY (id)
);

COMMENT ON COLUMN test_service_v1.drift_event.id                   IS 'Unique drift event identifier';
COMMENT ON COLUMN test_service_v1.drift_event.sync_record_id       IS 'UUID of the viewer synchronization record for which the drift was detected';
COMMENT ON COLUMN test_service_v1.drift_event.projected_version_id IS 'UUID of the immutable domain version expected to be represented when the drift was detected';
COMMENT ON COLUMN test_service_v1.drift_event.detected_at          IS 'Drift detection timestamp';
COMMENT ON COLUMN test_service_v1.drift_event.drift_type           IS 'Type of difference detected: MODIFIED, DELETED, or MISSING';
COMMENT ON COLUMN test_service_v1.drift_event.notification_status  IS 'Delivery status of the drift notification: PENDING, SENT, or ERROR';
COMMENT ON COLUMN test_service_v1.drift_event.details              IS 'Structured details describing the detected difference; must not contain secrets or large payloads';
COMMENT ON COLUMN test_service_v1.drift_event.created_at           IS 'Timestamp when the drift event record was created';

CREATE INDEX IF NOT EXISTS idx_drift_event_sync_record_id       ON test_service_v1.drift_event (sync_record_id);
CREATE INDEX IF NOT EXISTS idx_drift_event_notification_status  ON test_service_v1.drift_event (notification_status);
