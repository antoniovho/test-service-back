"""Temporary CLI entry point for the first corpus load."""

import argparse
import asyncio
from pathlib import Path

from test_service.bootstrap.container import get_injector
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
from test_service.infrastructure.adapters.input.cli.corpus_importer import CorpusImporter


def main() -> None:
    """Parse first-load arguments and run the temporary importer."""
    parser = argparse.ArgumentParser(description="Import strict Test Service corpus documents")
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--requested-by", required=True)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    report = asyncio.run(
        _run(arguments.corpus_dir, arguments.project_key, arguments.requested_by, arguments.dry_run)
    )
    print(report)


async def _run(directory: Path, project_key: str, requested_by: str, dry_run: bool) -> object:
    injector = get_injector()
    importer = CorpusImporter(
        injector.inject(CreatePreconditionUseCase),
        injector.inject(CreateTestCaseUseCase),
        injector.inject(PreconditionPersistencePort),
        injector.inject(TestCasePersistencePort),
    )
    return await importer.import_directory(directory, project_key, requested_by, dry_run)
