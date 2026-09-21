SET search_path TO test_service, public;

CREATE OR REPLACE FUNCTION enforce_versioned_content_immutability()
RETURNS trigger AS $$
BEGIN
  IF to_jsonb(NEW) - ARRAY['status'] IS DISTINCT FROM to_jsonb(OLD) - ARRAY['status'] THEN
    RAISE EXCEPTION 'Versioned entity content is immutable; create a new version';
  END IF;

  IF NOT (
    NEW.status = OLD.status OR
    (OLD.status = 'DRAFT' AND NEW.status = 'ACTIVE') OR
    (OLD.status = 'ACTIVE' AND NEW.status = 'DEPRECATED')
  ) THEN
    RAISE EXCEPTION 'Invalid lifecycle transition: % -> %', OLD.status, NEW.status;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_test_cases_immutable
BEFORE UPDATE ON test_cases
FOR EACH ROW EXECUTE FUNCTION enforce_versioned_content_immutability();

CREATE TRIGGER trg_test_preconditions_immutable
BEFORE UPDATE ON test_preconditions
FOR EACH ROW EXECUTE FUNCTION enforce_versioned_content_immutability();

CREATE TRIGGER trg_test_sets_immutable
BEFORE UPDATE ON test_sets
FOR EACH ROW EXECUTE FUNCTION enforce_versioned_content_immutability();

CREATE TRIGGER trg_test_plans_immutable
BEFORE UPDATE ON test_plans
FOR EACH ROW EXECUTE FUNCTION enforce_versioned_content_immutability();

CREATE OR REPLACE FUNCTION enforce_snapshot_relationship_immutability()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'Snapshot relationships are immutable; create a new version';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_test_case_preconditions_immutable
BEFORE UPDATE OR DELETE ON test_case_preconditions
FOR EACH ROW EXECUTE FUNCTION enforce_snapshot_relationship_immutability();

CREATE TRIGGER trg_test_set_items_immutable
BEFORE UPDATE OR DELETE ON test_set_items
FOR EACH ROW EXECUTE FUNCTION enforce_snapshot_relationship_immutability();

CREATE TRIGGER trg_test_plan_test_sets_immutable
BEFORE UPDATE OR DELETE ON test_plan_test_sets
FOR EACH ROW EXECUTE FUNCTION enforce_snapshot_relationship_immutability();

CREATE TRIGGER trg_test_plan_test_cases_immutable
BEFORE UPDATE OR DELETE ON test_plan_test_cases
FOR EACH ROW EXECUTE FUNCTION enforce_snapshot_relationship_immutability();

CREATE OR REPLACE FUNCTION enforce_relationship_project_consistency()
RETURNS trigger AS $$
DECLARE
  parent_project_key VARCHAR(20);
  child_project_key VARCHAR(20);
BEGIN
  IF TG_TABLE_NAME = 'test_case_preconditions' THEN
    SELECT project_key INTO parent_project_key FROM test_cases WHERE id = NEW.test_case_id;
    SELECT project_key INTO child_project_key FROM test_preconditions WHERE id = NEW.precondition_id;
  ELSIF TG_TABLE_NAME = 'test_set_items' THEN
    SELECT project_key INTO parent_project_key FROM test_sets WHERE id = NEW.test_set_id;
    SELECT project_key INTO child_project_key FROM test_cases WHERE id = NEW.test_case_id;
  ELSIF TG_TABLE_NAME = 'test_plan_test_sets' THEN
    SELECT project_key INTO parent_project_key FROM test_plans WHERE id = NEW.test_plan_id;
    SELECT project_key INTO child_project_key FROM test_sets WHERE id = NEW.test_set_id;
  ELSIF TG_TABLE_NAME = 'test_plan_test_cases' THEN
    SELECT project_key INTO parent_project_key FROM test_plans WHERE id = NEW.test_plan_id;
    SELECT project_key INTO child_project_key FROM test_cases WHERE id = NEW.test_case_id;
  END IF;

  IF parent_project_key IS DISTINCT FROM child_project_key THEN
    RAISE EXCEPTION 'Snapshot relationships must belong to the same project';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_test_case_preconditions_same_project
BEFORE INSERT ON test_case_preconditions
FOR EACH ROW EXECUTE FUNCTION enforce_relationship_project_consistency();

CREATE TRIGGER trg_test_set_items_same_project
BEFORE INSERT ON test_set_items
FOR EACH ROW EXECUTE FUNCTION enforce_relationship_project_consistency();

CREATE TRIGGER trg_test_plan_test_sets_same_project
BEFORE INSERT ON test_plan_test_sets
FOR EACH ROW EXECUTE FUNCTION enforce_relationship_project_consistency();

CREATE TRIGGER trg_test_plan_test_cases_same_project
BEFORE INSERT ON test_plan_test_cases
FOR EACH ROW EXECUTE FUNCTION enforce_relationship_project_consistency();
