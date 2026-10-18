import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from test_service.domain.model.exceptions import (
    test_case_already_exists_exception,
)
from test_service.domain.model.exceptions.precondition_already_exists_exception import (
    PreconditionAlreadyExistsException,
)
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
        "schemaVersion": "1.2.0",
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
        "schemaVersion": "1.2.0",
        "preconditionKey": "DEPENDENCY-HEALTH",
        "summary": "Dependency is healthy",
        "validationDefinition": _valid_document()["definition"],
    }


def _reference(key: str) -> list[dict[str, object]]:
    return [{"preconditionKey": key, "version": 1}]


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

    def test_when_sensitive_header_uses_captured_variable_expect_document_accepted(
        self, tmp_path
    ) -> None:
        document = _valid_document()
        action = document["definition"]["actions"][0]
        action["configuration"]["headers"] = {"Authorization": "Bearer {generated_api_key}"}
        path = tmp_path / "captured-secret.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        loaded = load_document(path)

        assert (
            loaded.definition.actions[0].configuration["headers"]["Authorization"]
            == "Bearer {generated_api_key}"
        )

    def test_when_forbidden_text_assertion_is_valid_expect_document_accepted(
        self, tmp_path
    ) -> None:
        document = _valid_document()
        action = document["definition"]["actions"][0]
        action["configuration"]["forbiddenText"] = ["secret-key", "Traceback"]
        path = tmp_path / "forbidden-text.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        loaded = load_document(path)

        assert loaded.definition.actions[0].configuration["forbiddenText"] == [
            "secret-key",
            "Traceback",
        ]

    def test_when_document_violates_contract_expect_document_rejected(self, tmp_path) -> None:
        document = _valid_document()
        document["metadata"] = {"labels": ["duplicate", "duplicate"]}
        path = tmp_path / "invalid-contract.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        with pytest.raises(ValueError, match="does not satisfy corpus contract"):
            load_document(path)

    @pytest.mark.parametrize(
        "content",
        ["{", json.dumps([_valid_document()])],
        ids=["invalid-json", "json-array"],
    )
    def test_when_document_cannot_be_parsed_as_a_json_object_expect_error(
        self, tmp_path, content
    ) -> None:
        path = tmp_path / "invalid.json"
        path.write_text(content, encoding="utf-8")

        with pytest.raises(ValueError, match="cannot read corpus document|must be a JSON object"):
            load_document(path)


class TestCorpusImporter:
    async def test_when_directory_does_not_exist_expect_error(self, tmp_path) -> None:
        importer = CorpusImporter(AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())

        with pytest.raises(ValueError, match="does not exist"):
            await importer.import_directory(tmp_path / "missing", "PROJECT", "migration")

    async def test_when_no_files_are_selected_expect_error(self) -> None:
        importer = CorpusImporter(AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())

        with pytest.raises(ValueError, match="selected files does not contain JSON documents"):
            await importer.import_files(
                (), "PROJECT", "migration", source_description="selected files"
            )

    async def test_when_selecting_files_expect_only_those_documents_imported(
        self, tmp_path
    ) -> None:
        precondition = _valid_precondition()
        test_case = _valid_document()
        test_case["preconditionReferences"] = _reference("DEPENDENCY-HEALTH")
        precondition_path = tmp_path / "precondition.json"
        test_case_path = tmp_path / "test-case.json"
        precondition_path.write_text(json.dumps(precondition), encoding="utf-8")
        test_case_path.write_text(json.dumps(test_case), encoding="utf-8")
        precondition_identifier = uuid4()
        create_precondition = AsyncMock()
        create_precondition.execute.return_value = SimpleNamespace(
            identifier=precondition_identifier
        )
        create_test_case = AsyncMock()
        precondition_repository = AsyncMock()
        test_case_repository = AsyncMock()
        precondition_repository.find_latest_version.return_value = None
        precondition_repository.find_by_key_and_version.return_value = SimpleNamespace(
            identifier=precondition_identifier
        )
        test_case_repository.find_latest_version.return_value = None
        importer = CorpusImporter(
            create_precondition,
            create_test_case,
            precondition_repository,
            test_case_repository,
        )

        report = await importer.import_files(
            [test_case_path, precondition_path], "PROJECT", "migration"
        )

        assert report.created_preconditions == 1
        assert report.created_test_cases == 1
        assert create_test_case.execute.await_args.args[0].preconditions == (
            precondition_identifier,
        )

    async def test_when_dry_run_references_new_precondition_expect_simulated_import(
        self, tmp_path
    ) -> None:
        precondition = _valid_precondition()
        test_case = _valid_document()
        test_case["preconditionReferences"] = _reference("DEPENDENCY-HEALTH")
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

    async def test_when_precondition_exists_expect_explicit_version_used_for_reference(
        self, tmp_path
    ) -> None:
        precondition = _valid_precondition()
        test_case = _valid_document()
        test_case["preconditionReferences"] = _reference("DEPENDENCY-HEALTH")
        (tmp_path / "01-precondition.json").write_text(json.dumps(precondition), encoding="utf-8")
        (tmp_path / "02-test-case.json").write_text(json.dumps(test_case), encoding="utf-8")
        existing_identifier = uuid4()
        create_precondition = AsyncMock()
        create_test_case = AsyncMock()
        precondition_repository = AsyncMock()
        test_case_repository = AsyncMock()
        precondition_repository.find_latest_version.return_value = 2
        precondition_repository.find_by_key_and_version.return_value = SimpleNamespace(
            identifier=existing_identifier
        )
        test_case_repository.find_latest_version.return_value = None
        importer = CorpusImporter(
            create_precondition,
            create_test_case,
            precondition_repository,
            test_case_repository,
        )

        report = await importer.import_directory(tmp_path, "PROJECT", "migration")

        assert report.skipped_preconditions == 1
        assert report.created_test_cases == 1
        precondition_repository.find_by_key_and_version.assert_awaited_once_with(
            "PROJECT", "DEPENDENCY-HEALTH", 1
        )
        assert create_test_case.execute.await_args.args[0].preconditions == (existing_identifier,)

    async def test_when_importing_new_documents_expect_authoring_commands_executed(
        self, tmp_path
    ) -> None:
        precondition = _valid_precondition()
        test_case = _valid_document()
        test_case["preconditionReferences"] = _reference("DEPENDENCY-HEALTH")
        (tmp_path / "01-precondition.json").write_text(json.dumps(precondition), encoding="utf-8")
        (tmp_path / "02-test-case.json").write_text(json.dumps(test_case), encoding="utf-8")
        precondition_identifier = uuid4()
        create_precondition = AsyncMock()
        create_precondition.execute.return_value = SimpleNamespace(
            identifier=precondition_identifier
        )
        create_test_case = AsyncMock()
        precondition_repository = AsyncMock()
        test_case_repository = AsyncMock()
        precondition_repository.find_latest_version.return_value = None
        precondition_repository.find_by_key_and_version.return_value = SimpleNamespace(
            identifier=precondition_identifier
        )
        test_case_repository.find_latest_version.return_value = None
        importer = CorpusImporter(
            create_precondition,
            create_test_case,
            precondition_repository,
            test_case_repository,
        )

        report = await importer.import_directory(tmp_path, "PROJECT", "migration")

        assert report.created_preconditions == 1
        assert report.created_test_cases == 1
        create_precondition.execute.assert_awaited_once()
        create_test_case.execute.assert_awaited_once()
        assert create_test_case.execute.await_args.args[0].preconditions == (
            precondition_identifier,
        )

    async def test_when_precondition_is_created_concurrently_expect_import_skipped(
        self, tmp_path
    ) -> None:
        (tmp_path / "precondition.json").write_text(
            json.dumps(_valid_precondition()), encoding="utf-8"
        )
        create_precondition = AsyncMock()
        create_precondition.execute.side_effect = PreconditionAlreadyExistsException(
            "PROJECT", "DEPENDENCY-HEALTH"
        )
        create_test_case = AsyncMock()
        precondition_repository = AsyncMock()
        test_case_repository = AsyncMock()
        precondition_repository.find_latest_version.side_effect = [None, object()]
        importer = CorpusImporter(
            create_precondition,
            create_test_case,
            precondition_repository,
            test_case_repository,
        )

        report = await importer.import_directory(tmp_path, "PROJECT", "migration")

        assert report.skipped_preconditions == 1
        create_precondition.execute.assert_awaited_once()
        create_test_case.execute.assert_not_awaited()

    async def test_when_explicit_precondition_version_is_missing_expect_error(
        self, tmp_path
    ) -> None:
        test_case = _valid_document()
        test_case["preconditionReferences"] = _reference("DEPENDENCY-HEALTH")
        (tmp_path / "test-case.json").write_text(json.dumps(test_case), encoding="utf-8")
        precondition_repository = AsyncMock()
        precondition_repository.find_by_key_and_version.return_value = None
        test_case_repository = AsyncMock()
        test_case_repository.find_latest_version.return_value = None
        importer = CorpusImporter(
            AsyncMock(), AsyncMock(), precondition_repository, test_case_repository
        )

        with pytest.raises(ValueError, match="DEPENDENCY-HEALTH.*version 1 does not exist"):
            await importer.import_directory(tmp_path, "PROJECT", "migration")

    async def test_when_test_case_references_unknown_precondition_expect_error(
        self, tmp_path
    ) -> None:
        test_case = _valid_document()
        test_case["preconditionReferences"] = [{"preconditionKey": "MISSING", "version": 1}]
        (tmp_path / "test-case.json").write_text(json.dumps(test_case), encoding="utf-8")
        test_case_repository = AsyncMock()
        test_case_repository.find_latest_version.return_value = None
        precondition_repository = AsyncMock()
        precondition_repository.find_by_key_and_version.return_value = None
        importer = CorpusImporter(
            AsyncMock(), AsyncMock(), precondition_repository, test_case_repository
        )

        with pytest.raises(ValueError, match="MISSING.*version 1 does not exist"):
            await importer.import_directory(tmp_path, "PROJECT", "migration")

    async def test_when_test_case_is_created_concurrently_expect_it_skipped(self, tmp_path) -> None:
        (tmp_path / "test-case.json").write_text(json.dumps(_valid_document()), encoding="utf-8")
        create_test_case = AsyncMock()
        create_test_case.execute.side_effect = (
            test_case_already_exists_exception.TestCaseAlreadyExistsException(
                "PROJECT", "GW-INT-007"
            )
        )
        test_case_repository = AsyncMock()
        test_case_repository.find_latest_version.return_value = None
        importer = CorpusImporter(AsyncMock(), create_test_case, AsyncMock(), test_case_repository)

        report = await importer.import_directory(tmp_path, "PROJECT", "migration")

        assert report.skipped_test_cases == 1
        create_test_case.execute.assert_awaited_once()

    async def test_when_test_case_already_exists_expect_it_skipped(self, tmp_path) -> None:
        (tmp_path / "test-case.json").write_text(json.dumps(_valid_document()), encoding="utf-8")
        test_case_repository = AsyncMock()
        test_case_repository.find_latest_version.return_value = object()
        importer = CorpusImporter(AsyncMock(), AsyncMock(), AsyncMock(), test_case_repository)

        report = await importer.import_directory(tmp_path, "PROJECT", "migration")

        assert report.skipped_test_cases == 1

    async def test_when_concurrent_precondition_is_not_persisted_expect_original_error(
        self, tmp_path
    ) -> None:
        (tmp_path / "precondition.json").write_text(
            json.dumps(_valid_precondition()), encoding="utf-8"
        )
        create_precondition = AsyncMock()
        create_precondition.execute.side_effect = PreconditionAlreadyExistsException(
            "PROJECT", "DEPENDENCY-HEALTH"
        )
        precondition_repository = AsyncMock()
        precondition_repository.find_latest_version.side_effect = [None, None]
        importer = CorpusImporter(
            create_precondition, AsyncMock(), precondition_repository, AsyncMock()
        )

        with pytest.raises(PreconditionAlreadyExistsException):
            await importer.import_directory(tmp_path, "PROJECT", "migration")
