"""Strict, removable importer for the Test Service first-load corpus."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from uuid import UUID, uuid4

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from test_service.domain.application.commands.authoring import (
    CreatePreconditionCommand,
    CreateTestCaseCommand,
)
from test_service.domain.application.queries.pagination import PaginationParams, SortOrder
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.exceptions.precondition_already_exists_exception import (
    PreconditionAlreadyExistsException,
)
from test_service.domain.model.exceptions.test_case_already_exists_exception import (
    TestCaseAlreadyExistsException,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCase,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)
from test_service.infrastructure.adapters.input.cli.dtos.corpus_dtos import (
    CorpusDefinition,
    CorpusDocument,
    PreconditionCorpusDocument,
    TestCaseCorpusDocument,
)


@dataclass(frozen=True, slots=True)
class ImportReport:
    """Counters emitted by one corpus import attempt."""

    created_preconditions: int = 0
    skipped_preconditions: int = 0
    created_test_cases: int = 0
    skipped_test_cases: int = 0


class CorpusImporter:
    """Import strict documents in precondition-first order through authoring ports."""

    def __init__(
        self,
        create_precondition: CreatePreconditionUseCase,
        create_test_case: CreateTestCaseUseCase,
        precondition_repository: PreconditionPersistencePort,
        test_case_repository: TestCasePersistencePort,
    ) -> None:
        self._create_precondition = create_precondition
        self._create_test_case = create_test_case
        self._precondition_repository = precondition_repository
        self._test_case_repository = test_case_repository

    async def import_directory(
        self,
        directory: Path,
        project_key: str,
        requested_by: str,
        dry_run: bool = False,
    ) -> ImportReport:
        """Validate and import all JSON documents found below a corpus directory."""
        documents = tuple(_load_documents(directory))
        preconditions = tuple(
            item for item in documents if isinstance(item, PreconditionCorpusDocument)
        )
        test_cases = tuple(item for item in documents if isinstance(item, TestCaseCorpusDocument))
        precondition_ids, report = await self._import_preconditions(
            preconditions, project_key, requested_by, dry_run
        )
        test_case_report = await self._import_test_cases(
            test_cases, precondition_ids, project_key, requested_by, dry_run
        )
        return ImportReport(
            report.created_preconditions,
            report.skipped_preconditions,
            test_case_report.created_test_cases,
            test_case_report.skipped_test_cases,
        )

    async def _import_preconditions(
        self,
        documents: Iterable[PreconditionCorpusDocument],
        project_key: str,
        requested_by: str,
        dry_run: bool,
    ) -> tuple[dict[str, UUID], ImportReport]:
        identifiers: dict[str, UUID] = {}
        report = ImportReport()
        for document in documents:
            existing = await self._precondition_repository.find_latest_version(
                project_key, document.precondition_key
            )
            if existing is not None:
                identifiers[document.precondition_key] = await self._latest_precondition_identifier(
                    project_key, document.precondition_key
                )
                report = ImportReport(
                    report.created_preconditions,
                    report.skipped_preconditions + 1,
                    report.created_test_cases,
                    report.skipped_test_cases,
                )
                continue
            if dry_run:
                identifiers[document.precondition_key] = uuid4()
                report = ImportReport(
                    report.created_preconditions + 1,
                    report.skipped_preconditions,
                    report.created_test_cases,
                    report.skipped_test_cases,
                )
                continue
            try:
                created = await self._create_precondition.execute(
                    CreatePreconditionCommand(
                        project_key=project_key,
                        precondition_key=document.precondition_key,
                        name=document.summary,
                        description=document.metadata.objective or document.summary,
                        validation_definition=_definition(document.validation_definition),
                        requested_by=requested_by,
                        requested_at=datetime.now(UTC),
                        metadata=document.metadata.model_dump(exclude_none=True),
                    )
                )
            except PreconditionAlreadyExistsException:
                existing = await self._precondition_repository.find_latest_version(
                    project_key, document.precondition_key
                )
                if existing is None:
                    raise
                identifiers[document.precondition_key] = await self._latest_precondition_identifier(
                    project_key, document.precondition_key
                )
                report = ImportReport(
                    report.created_preconditions,
                    report.skipped_preconditions + 1,
                    report.created_test_cases,
                    report.skipped_test_cases,
                )
            else:
                identifiers[document.precondition_key] = created.identifier
                report = ImportReport(
                    report.created_preconditions + 1,
                    report.skipped_preconditions,
                    report.created_test_cases,
                    report.skipped_test_cases,
                )
        return identifiers, report

    async def _latest_precondition_identifier(
        self, project_key: str, precondition_key: str
    ) -> UUID:
        snapshots = await self._precondition_repository.find_versions(
            project_key,
            precondition_key,
            PaginationParams(limit=1, sort_by="version", order=SortOrder.DESC),
        )
        if not snapshots.items:
            raise ValueError(f"precondition '{precondition_key}' has no persisted snapshot")
        return snapshots.items[0].identifier

    async def _import_test_cases(
        self,
        documents: Iterable[TestCaseCorpusDocument],
        precondition_ids: Mapping[str, UUID],
        project_key: str,
        requested_by: str,
        dry_run: bool,
    ) -> ImportReport:
        report = ImportReport()
        for document in documents:
            existing = await self._test_case_repository.find_latest_version(
                project_key, document.test_case_key
            )
            if existing is not None:
                report = ImportReport(
                    report.created_preconditions,
                    report.skipped_preconditions,
                    report.created_test_cases,
                    report.skipped_test_cases + 1,
                )
                continue
            missing = set(document.precondition_keys) - set(precondition_ids)
            if missing:
                raise ValueError(
                    f"test case '{document.test_case_key}' references unavailable preconditions "
                    f"{sorted(missing)}"
                )
            if dry_run:
                report = ImportReport(
                    report.created_preconditions,
                    report.skipped_preconditions,
                    report.created_test_cases + 1,
                    report.skipped_test_cases,
                )
                continue
            try:
                await self._create_test_case.execute(
                    CreateTestCaseCommand(
                        project_key=project_key,
                        test_key=document.test_case_key,
                        name=document.summary,
                        summary=document.summary,
                        objective=document.metadata.objective or document.summary,
                        test_type=document.test_type,
                        test_level=document.test_level,
                        priority=document.priority,
                        definition=_definition(document.definition),
                        timeout_seconds=document.timeout_seconds,
                        requested_by=requested_by,
                        requested_at=datetime.now(UTC),
                        preconditions=tuple(
                            precondition_ids[key] for key in document.precondition_keys
                        ),
                        metadata=document.metadata.model_dump(exclude_none=True),
                    )
                )
            except TestCaseAlreadyExistsException:
                report = ImportReport(
                    report.created_preconditions,
                    report.skipped_preconditions,
                    report.created_test_cases,
                    report.skipped_test_cases + 1,
                )
            else:
                report = ImportReport(
                    report.created_preconditions,
                    report.skipped_preconditions,
                    report.created_test_cases + 1,
                    report.skipped_test_cases,
                )
        return report


def load_document(path: Path) -> CorpusDocument:
    """Load one strict JSON document and reject unsupported corpus versions."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read corpus document '{path}'") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"corpus document '{path}' must be a JSON object")
    validation_error = next(_corpus_validator().iter_errors(payload), None)
    if validation_error is not None:
        raise ValueError(
            f"corpus document '{path}' does not satisfy corpus contract: {validation_error.message}"
        )
    try:
        if payload.get("kind") == "precondition":
            return PreconditionCorpusDocument.model_validate(payload)
        return TestCaseCorpusDocument.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"invalid corpus document '{path}': {exc}") from exc


def _load_documents(directory: Path) -> Iterable[CorpusDocument]:
    if not directory.is_dir():
        raise ValueError(f"corpus directory '{directory}' does not exist")
    yield from (load_document(path) for path in sorted(directory.rglob("*.json")))


@lru_cache
def _corpus_validator() -> Draft202012Validator:
    schema_path = Path(__file__).parents[5] / "contracts/corpus/test-corpus-1.1.0.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("cannot load corpus contract schema") from exc
    return Draft202012Validator(schema)


def _definition(document: CorpusDefinition) -> Definition:
    return Definition(
        variables=document.variables,
        actions=tuple(
            Action(item.identifier, item.action_type, item.configuration)
            for item in document.actions
        ),
        schema_version=document.schema_version,
    )
