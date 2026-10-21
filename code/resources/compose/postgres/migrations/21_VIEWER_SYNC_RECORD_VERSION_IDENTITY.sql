-- Migrates existing Viewer sync records from logical-key to immutable-version identity.

ALTER TABLE test_service_v1.viewer_sync_record
    ADD COLUMN IF NOT EXISTS entity_version integer;

-- Recover the immutable version from the persisted snapshot UUID. Rows that predate
-- versioned projections retain v1 as a safe legacy fallback.
UPDATE test_service_v1.viewer_sync_record record
SET entity_version = COALESCE(
    record.entity_version,
    precondition.version,
    test_case.version,
    test_set.version,
    test_plan.version,
    1
)
FROM test_service_v1.viewer_sync_record source
LEFT JOIN test_service_v1.precondition precondition
    ON source.entity_type = 'PRECONDITION' AND precondition.id = source.projected_version_id
LEFT JOIN test_service_v1.test_case test_case
    ON source.entity_type = 'TEST_CASE' AND test_case.id = source.projected_version_id
LEFT JOIN test_service_v1.test_set test_set
    ON source.entity_type = 'TEST_SET' AND test_set.id = source.projected_version_id
LEFT JOIN test_service_v1.test_plan test_plan
    ON source.entity_type = 'TEST_PLAN' AND test_plan.id = source.projected_version_id
WHERE record.id = source.id
  AND record.entity_version IS NULL;

ALTER TABLE test_service_v1.viewer_sync_record
    ALTER COLUMN entity_version SET NOT NULL;

ALTER TABLE test_service_v1.viewer_sync_record
    DROP CONSTRAINT IF EXISTS viewer_sync_record_entity_viewer_uq;

ALTER TABLE test_service_v1.viewer_sync_record
    ADD CONSTRAINT viewer_sync_record_entity_viewer_uq
    UNIQUE (project_key, entity_type, entity_key, entity_version, viewer_type);
