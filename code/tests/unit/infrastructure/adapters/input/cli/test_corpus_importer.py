import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import Page
from test_service.infrastructure.adapters.input.cli.corpus_importer import (
    CorpusImporter,
    load_document,
)
from test_service.infrastructure.adapters.input.cli.dtos.corpus_dtos import (
    TestCaseCorpusDocument as CorpusTestCase,
)


def _valid_document() -> dict[str, object]:
    return {
        "kind": "test-case",
        "schemaVersion": "1.1.0",
        "testCaseKey": "GW-INT-007",
        "summary": "Returns a healthy dependency state",
        "definition": {
            "schemaVersion": "1.1",
            "variables": {"baseUrl": "https://api.example.test"},
            "actions": [
                {
                    "id": "health",
                    "type": "HTTP",
                    "configuration": {
                        "url": "{{baseUrl}}/health",
                        "expectedStatus": 200,
                    },
                }
            ],
        },
    }


def _valid_precondition() -> dict[str, object]:
    return {
        "kind": "precondition",
        "schemaVersion": "1.1.0",
        "preconditionKey": "DEPENDENCY-HEALTH",
        "summary": "Dependency is healthy",
        "validationDefinition": _valid_document()["definition"],
    }


class TestLoadDocument:
    def test_when_document_is_strict_version_expect_test_case_dto(self, tmp_path) -> None:
        path = tmp_path / "health.json"
        path.write_text(json.dumps(_valid_document()), encoding="utf-8")

        document = load_document(path)

        assert isinstance(document, CorpusTestCase)
        assert document.definition.actions[0].configuration["expectedStatus"] == 200

    def test_when_sensitive_header_is_literal_expect_document_rejected(self, tmp_path) -> None:
        document = _valid_document()
        action = document["definition"]["actions"][0]
        action["configuration"]["headers"] = {"Authorization": "Bearer literal-secret"}
        path = tmp_path / "unsafe.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        with pytest.raises(ValueError, match="sensitive header 'Authorization'"):
            load_document(path)

    def test_when_document_violates_contract_expect_document_rejected(self, tmp_path) -> None:
        document = _valid_document()
        document["metadata"] = {"labels": ["duplicate", "duplicate"]}
        path = tmp_path / "invalid-contract.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        with pytest.raises(ValueError, match="does not satisfy corpus contract"):
            load_document(path)


class TestCorpusImporter:
    async def test_when_dry_run_references_new_precondition_expect_simulated_import(
        self, tmp_path
    ) -> None:
        precondition = _valid_precondition()
        test_case = _valid_document()
        test_case["preconditionKeys"] = ["DEPENDENCY-HEALTH"]
        (tmp_path / "01-precondition.json").write_text(json.dumps(precondition), encoding="utf-8")
        (tmp_path / "02-test-case.json").write_text(json.dumps(test_case), encoding="utf-8")
        create_precondition = AsyncMock()
        create_test_case = AsyncMock()
        precondition_repository = AsyncMock()
        test_case_repository = AsyncMock()
        precondition_repository.find_latest_version.return_value = None
        test_case_repository.find_latest_version.return_value = None
        importer = CorpusImporter(
            create_precondition,
            create_test_case,
            precondition_repository,
            test_case_repository,
        )

        report = await importer.import_directory(tmp_path, "PROJECT", "migration", dry_run=True)

        assert report.created_preconditions == 1
        assert report.created_test_cases == 1
        create_precondition.execute.assert_not_awaited()
        create_test_case.execute.assert_not_awaited()

    async def test_when_precondition_exists_expect_latest_snapshot_used_for_reference(
        self, tmp_path
    ) -> None:
        precondition = _valid_precondition()
        test_case = _valid_document()
        test_case["preconditionKeys"] = ["DEPENDENCY-HEALTH"]
        (tmp_path / "01-precondition.json").write_text(json.dumps(precondition), encoding="utf-8")
        (tmp_path / "02-test-case.json").write_text(json.dumps(test_case), encoding="utf-8")
        existing_identifier = uuid4()
        create_precondition = AsyncMock()
        create_test_case = AsyncMock()
        precondition_repository = AsyncMock()
        test_case_repository = AsyncMock()
        precondition_repository.find_latest_version.return_value = 2
        precondition_repository.find_versions.return_value = Page(
            (SimpleNamespace(identifier=existing_identifier),), 1
        )
        test_case_repository.find_latest_version.return_value = None
        importer = CorpusImporter(
            create_precondition,
            create_test_case,
            precondition_repository,
            test_case_repository,
        )

        report = await importer.import_directory(tmp_path, "PROJECT", "migration", dry_run=True)

        assert report.skipped_preconditions == 1
        assert report.created_test_cases == 1
        precondition_repository.find_versions.assert_awaited_once()
