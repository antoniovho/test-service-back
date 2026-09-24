-- Foreign keys and check constraints (idempotent guards)

DO $$
DECLARE
    v_fk_type  CONSTANT TEXT := 'FOREIGN KEY';
    v_chk_type CONSTANT TEXT := 'CHECK';
BEGIN
    -- precondition -> project FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_precondition_project'
          AND table_name      = 'precondition'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.precondition
            ADD CONSTRAINT fk_precondition_project
            FOREIGN KEY (project_key)
            REFERENCES test_service_v1.project(key)
            ON DELETE RESTRICT;
    END IF;

    -- test_case -> project FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_case_project'
          AND table_name      = 'test_case'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_case
            ADD CONSTRAINT fk_test_case_project
            FOREIGN KEY (project_key)
            REFERENCES test_service_v1.project(key)
            ON DELETE RESTRICT;
    END IF;

    -- test_case_precondition -> test_case FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_case_precondition_test_case'
          AND table_name      = 'test_case_precondition'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_case_precondition
            ADD CONSTRAINT fk_test_case_precondition_test_case
            FOREIGN KEY (test_case_id)
            REFERENCES test_service_v1.test_case(id)
            ON DELETE CASCADE;
    END IF;

    -- test_case_precondition -> precondition FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_case_precondition_precondition'
          AND table_name      = 'test_case_precondition'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_case_precondition
            ADD CONSTRAINT fk_test_case_precondition_precondition
            FOREIGN KEY (precondition_id)
            REFERENCES test_service_v1.precondition(id)
            ON DELETE RESTRICT;
    END IF;

    -- test_set -> project FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_set_project'
          AND table_name      = 'test_set'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_set
            ADD CONSTRAINT fk_test_set_project
            FOREIGN KEY (project_key)
            REFERENCES test_service_v1.project(key)
            ON DELETE RESTRICT;
    END IF;

    -- test_set_item -> test_set FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_set_item_test_set'
          AND table_name      = 'test_set_item'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_set_item
            ADD CONSTRAINT fk_test_set_item_test_set
            FOREIGN KEY (test_set_id)
            REFERENCES test_service_v1.test_set(id)
            ON DELETE CASCADE;
    END IF;

    -- test_set_item -> test_case FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_set_item_test_case'
          AND table_name      = 'test_set_item'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_set_item
            ADD CONSTRAINT fk_test_set_item_test_case
            FOREIGN KEY (test_case_id)
            REFERENCES test_service_v1.test_case(id)
            ON DELETE RESTRICT;
    END IF;

    -- test_plan -> project FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_plan_project'
          AND table_name      = 'test_plan'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan
            ADD CONSTRAINT fk_test_plan_project
            FOREIGN KEY (project_key)
            REFERENCES test_service_v1.project(key)
            ON DELETE RESTRICT;
    END IF;

    -- test_plan_test_set -> test_plan FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_plan_test_set_test_plan'
          AND table_name      = 'test_plan_test_set'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan_test_set
            ADD CONSTRAINT fk_test_plan_test_set_test_plan
            FOREIGN KEY (test_plan_id)
            REFERENCES test_service_v1.test_plan(id)
            ON DELETE CASCADE;
    END IF;

    -- test_plan_test_set -> test_set FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_plan_test_set_test_set'
          AND table_name      = 'test_plan_test_set'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan_test_set
            ADD CONSTRAINT fk_test_plan_test_set_test_set
            FOREIGN KEY (test_set_id)
            REFERENCES test_service_v1.test_set(id)
            ON DELETE RESTRICT;
    END IF;

    -- test_plan_test_case -> test_plan FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_plan_test_case_test_plan'
          AND table_name      = 'test_plan_test_case'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan_test_case
            ADD CONSTRAINT fk_test_plan_test_case_test_plan
            FOREIGN KEY (test_plan_id)
            REFERENCES test_service_v1.test_plan(id)
            ON DELETE CASCADE;
    END IF;

    -- test_plan_test_case -> test_case FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_plan_test_case_test_case'
          AND table_name      = 'test_plan_test_case'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan_test_case
            ADD CONSTRAINT fk_test_plan_test_case_test_case
            FOREIGN KEY (test_case_id)
            REFERENCES test_service_v1.test_case(id)
            ON DELETE RESTRICT;
    END IF;

    -- test_plan_exclusion -> test_plan FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_plan_exclusion_test_plan'
          AND table_name      = 'test_plan_exclusion'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan_exclusion
            ADD CONSTRAINT fk_test_plan_exclusion_test_plan
            FOREIGN KEY (test_plan_id)
            REFERENCES test_service_v1.test_plan(id)
            ON DELETE CASCADE;
    END IF;

    -- test_plan_exclusion -> test_case FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_plan_exclusion_test_case'
          AND table_name      = 'test_plan_exclusion'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan_exclusion
            ADD CONSTRAINT fk_test_plan_exclusion_test_case
            FOREIGN KEY (test_case_id)
            REFERENCES test_service_v1.test_case(id)
            ON DELETE RESTRICT;
    END IF;

    -- execution -> project FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_execution_project'
          AND table_name      = 'execution'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.execution
            ADD CONSTRAINT fk_execution_project
            FOREIGN KEY (project_key)
            REFERENCES test_service_v1.project(key)
            ON DELETE RESTRICT;
    END IF;

    -- execution -> test_plan FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_execution_test_plan'
          AND table_name      = 'execution'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.execution
            ADD CONSTRAINT fk_execution_test_plan
            FOREIGN KEY (test_plan_id)
            REFERENCES test_service_v1.test_plan(id)
            ON DELETE RESTRICT;
    END IF;

    -- execution -> environment FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_execution_environment'
          AND table_name      = 'execution'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.execution
            ADD CONSTRAINT fk_execution_environment
            FOREIGN KEY (environment_id)
            REFERENCES test_service_v1.environment(id)
            ON DELETE RESTRICT;
    END IF;

    -- test_result -> execution FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_result_execution'
          AND table_name      = 'test_result'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_result
            ADD CONSTRAINT fk_test_result_execution
            FOREIGN KEY (execution_id)
            REFERENCES test_service_v1.execution(id)
            ON DELETE CASCADE;
    END IF;

    -- test_result -> test_case FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_result_test_case'
          AND table_name      = 'test_result'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_result
            ADD CONSTRAINT fk_test_result_test_case
            FOREIGN KEY (test_case_id)
            REFERENCES test_service_v1.test_case(id)
            ON DELETE RESTRICT;
    END IF;

    -- action_result -> test_result FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_action_result_test_result'
          AND table_name      = 'action_result'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.action_result
            ADD CONSTRAINT fk_action_result_test_result
            FOREIGN KEY (test_result_id)
            REFERENCES test_service_v1.test_result(id)
            ON DELETE CASCADE;
    END IF;

    -- test_result_artifact -> test_result FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_result_artifact_test_result'
          AND table_name      = 'test_result_artifact'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_result_artifact
            ADD CONSTRAINT fk_test_result_artifact_test_result
            FOREIGN KEY (test_result_id)
            REFERENCES test_service_v1.test_result(id)
            ON DELETE CASCADE;
    END IF;

    -- test_result_artifact -> action_result FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_test_result_artifact_action_result'
          AND table_name      = 'test_result_artifact'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.test_result_artifact
            ADD CONSTRAINT fk_test_result_artifact_action_result
            FOREIGN KEY (action_result_id)
            REFERENCES test_service_v1.action_result(id)
            ON DELETE SET NULL;
    END IF;

    -- drift_event -> viewer_sync_record FK
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_drift_event_sync_record'
          AND table_name      = 'drift_event'
          AND constraint_type = v_fk_type
    ) THEN
        ALTER TABLE test_service_v1.drift_event
            ADD CONSTRAINT fk_drift_event_sync_record
            FOREIGN KEY (sync_record_id)
            REFERENCES test_service_v1.viewer_sync_record(id)
            ON DELETE CASCADE;
    END IF;

    -- project status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_project_status'
          AND table_name      = 'project'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.project
            ADD CONSTRAINT chk_project_status
            CHECK (status IN ('ACTIVE', 'DELETED'));
    END IF;

    -- precondition status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_precondition_status'
          AND table_name      = 'precondition'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.precondition
            ADD CONSTRAINT chk_precondition_status
            CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED'));
    END IF;

    -- test_case test_type check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_case_test_type'
          AND table_name      = 'test_case'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_case
            ADD CONSTRAINT chk_test_case_test_type
            CHECK (test_type IN ('AUTOMATED', 'MANUAL'));
    END IF;

    -- test_case test_level check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_case_test_level'
          AND table_name      = 'test_case'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_case
            ADD CONSTRAINT chk_test_case_test_level
            CHECK (test_level IN ('FUNCTIONAL', 'ERROR', 'INTEGRATION', 'PERFORMANCE', 'SECURITY', 'STRESS'));
    END IF;

    -- test_case priority check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_case_priority'
          AND table_name      = 'test_case'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_case
            ADD CONSTRAINT chk_test_case_priority
            CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'));
    END IF;

    -- test_case status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_case_status'
          AND table_name      = 'test_case'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_case
            ADD CONSTRAINT chk_test_case_status
            CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED'));
    END IF;

    -- test_set status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_set_status'
          AND table_name      = 'test_set'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_set
            ADD CONSTRAINT chk_test_set_status
            CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED'));
    END IF;

    -- test_plan status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_plan_status'
          AND table_name      = 'test_plan'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan
            ADD CONSTRAINT chk_test_plan_status
            CHECK (status IN ('DRAFT', 'ACTIVE', 'DEPRECATED'));
    END IF;

    -- test_plan execution_mode check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_plan_execution_mode'
          AND table_name      = 'test_plan'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_plan
            ADD CONSTRAINT chk_test_plan_execution_mode
            CHECK (execution_mode IN ('SEQUENTIAL', 'PARALLEL'));
    END IF;

    -- environment status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_environment_status'
          AND table_name      = 'environment'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.environment
            ADD CONSTRAINT chk_environment_status
            CHECK (status IN ('ACTIVE', 'INACTIVE', 'DEPRECATED'));
    END IF;

    -- execution trigger_type check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_execution_trigger_type'
          AND table_name      = 'execution'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.execution
            ADD CONSTRAINT chk_execution_trigger_type
            CHECK (trigger_type IN ('MANUAL', 'API', 'CI', 'SCHEDULE'));
    END IF;

    -- execution status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_execution_status'
          AND table_name      = 'execution'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.execution
            ADD CONSTRAINT chk_execution_status
            CHECK (status IN ('CREATED', 'RUNNING', 'PASSED', 'FAILED', 'PARTIALLY_FAILED', 'CANCELLED', 'ERROR'));
    END IF;

    -- test_result status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_result_status'
          AND table_name      = 'test_result'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_result
            ADD CONSTRAINT chk_test_result_status
            CHECK (status IN ('PASSED', 'FAILED', 'ERROR', 'BLOCKED', 'SKIPPED'));
    END IF;

    -- action_result status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_action_result_status'
          AND table_name      = 'action_result'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.action_result
            ADD CONSTRAINT chk_action_result_status
            CHECK (status IN ('PASSED', 'FAILED', 'ERROR', 'BLOCKED', 'SKIPPED'));
    END IF;

    -- test_result_artifact artifact_type check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_result_artifact_artifact_type'
          AND table_name      = 'test_result_artifact'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_result_artifact
            ADD CONSTRAINT chk_test_result_artifact_artifact_type
            CHECK (artifact_type IN ('REQUEST', 'RESPONSE', 'SSE_TRACE', 'LOG', 'OTHER'));
    END IF;

    -- test_result_artifact storage_type check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_test_result_artifact_storage_type'
          AND table_name      = 'test_result_artifact'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.test_result_artifact
            ADD CONSTRAINT chk_test_result_artifact_storage_type
            CHECK (storage_type IN ('DB', 'OBJECT_STORAGE'));
    END IF;

    -- viewer_sync_record entity_type check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_viewer_sync_record_entity_type'
          AND table_name      = 'viewer_sync_record'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.viewer_sync_record
            ADD CONSTRAINT chk_viewer_sync_record_entity_type
            CHECK (entity_type IN ('TEST_CASE', 'PRECONDITION', 'TEST_SET', 'TEST_PLAN'));
    END IF;

    -- viewer_sync_record viewer_type check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_viewer_sync_record_viewer_type'
          AND table_name      = 'viewer_sync_record'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.viewer_sync_record
            ADD CONSTRAINT chk_viewer_sync_record_viewer_type
            CHECK (viewer_type IN ('XRAY'));
    END IF;

    -- viewer_sync_record sync_status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_viewer_sync_record_sync_status'
          AND table_name      = 'viewer_sync_record'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.viewer_sync_record
            ADD CONSTRAINT chk_viewer_sync_record_sync_status
            CHECK (sync_status IN ('PENDING', 'SYNCED', 'ERROR', 'DRIFT_DETECTED'));
    END IF;

    -- drift_event drift_type check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_drift_event_drift_type'
          AND table_name      = 'drift_event'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.drift_event
            ADD CONSTRAINT chk_drift_event_drift_type
            CHECK (drift_type IN ('MODIFIED', 'DELETED', 'MISSING'));
    END IF;

    -- drift_event notification_status check
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_drift_event_notification_status'
          AND table_name      = 'drift_event'
          AND constraint_type = v_chk_type
    ) THEN
        ALTER TABLE test_service_v1.drift_event
            ADD CONSTRAINT chk_drift_event_notification_status
            CHECK (notification_status IN ('PENDING', 'SENT', 'ERROR'));
    END IF;
END $$;
