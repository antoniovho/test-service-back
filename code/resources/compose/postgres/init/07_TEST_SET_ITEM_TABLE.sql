-- Creates the test_set_item table (ordered test case versions belonging to a test set version)

CREATE TABLE IF NOT EXISTS test_service_v1.test_set_item (
    id           uuid    DEFAULT gen_random_uuid() NOT NULL,
    test_set_id  uuid    NOT NULL,
    test_case_id uuid    NOT NULL,
    position     INTEGER NOT NULL,
    CONSTRAINT test_set_item_pkey PRIMARY KEY (id),
    CONSTRAINT test_set_item_position_uq UNIQUE (test_set_id, position),
    CONSTRAINT test_set_item_test_set_test_case_uq UNIQUE (test_set_id, test_case_id)
);

COMMENT ON COLUMN test_service_v1.test_set_item.id           IS 'Unique row identifier';
COMMENT ON COLUMN test_service_v1.test_set_item.test_set_id  IS 'UUID of the test set version that contains the item';
COMMENT ON COLUMN test_service_v1.test_set_item.test_case_id IS 'UUID of the immutable test case version included in the set';
COMMENT ON COLUMN test_service_v1.test_set_item.position     IS 'Zero-based execution order of the test case within the set';

CREATE INDEX IF NOT EXISTS idx_test_set_item_test_set_id  ON test_service_v1.test_set_item (test_set_id);
CREATE INDEX IF NOT EXISTS idx_test_set_item_test_case_id ON test_service_v1.test_set_item (test_case_id);
