SET search_path TO test_service, public;

CREATE TABLE drift_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sync_record_id UUID NOT NULL REFERENCES viewer_sync_records(id) ON DELETE RESTRICT,
  projected_version_id UUID NOT NULL,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  drift_type VARCHAR(30) NOT NULL CHECK (drift_type IN ('MODIFIED', 'DELETED', 'MISSING')),
  notification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING'
    CHECK (notification_status IN ('PENDING', 'SENT', 'ERROR')),
  details JSONB
);
