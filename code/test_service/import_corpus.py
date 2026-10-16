"""Command-line importer for a selected Test Service corpus."""

import argparse
import asyncio
import json
from collections.abc import Sequence
from dataclasses import asdict
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
from test_service.infrastructure.adapters.input.cli.corpus_importer import (
    CorpusImporter,
    ImportReport,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_database_configuration import (  # noqa: E501
    PostgresDatabaseConfiguration,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import Test Service corpus JSON documents into an active project."
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--directory",
        type=Path,
        help="Import every JSON document below this directory.",
    )
    selection.add_argument(
        "--file",
        dest="files",
        type=Path,
        action="append",
        help="Import one JSON document; repeat the option to select several.",
    )
    parser.add_argument("--project-key", required=True, help="Active Test Service project key.")
    parser.add_argument(
        "--requested-by",
        required=True,
        help="Technical identity recorded as the creator of imported versions.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report the import without persisting changes.",
    )
    return parser


def _importer() -> CorpusImporter:
    injector = get_injector()
    return CorpusImporter(
        injector.inject(CreatePreconditionUseCase),
        injector.inject(CreateTestCaseUseCase),
        injector.inject(PreconditionPersistencePort),
        injector.inject(TestCasePersistencePort),
    )


async def run_import(arguments: argparse.Namespace) -> ImportReport:
    """Run one import and release the command's database resources afterwards."""
    injector = get_injector()
    try:
        importer = _importer()
        if arguments.directory is not None:
            return await importer.import_directory(
                arguments.directory,
                arguments.project_key,
                arguments.requested_by,
                arguments.dry_run,
            )
        return await importer.import_files(
            arguments.files,
            arguments.project_key,
            arguments.requested_by,
            arguments.dry_run,
        )
    finally:
        database = injector.inject(PostgresDatabaseConfiguration)
        await database.dispose()


def main(argv: Sequence[str] | None = None) -> None:
    """Parse CLI arguments, import the selected corpus, and print its report."""
    arguments = _parser().parse_args(argv)
    try:
        report = asyncio.run(run_import(arguments))
    except ValueError as exc:
        _parser().error(str(exc))
    print(json.dumps(asdict(report), sort_keys=True))


if __name__ == "__main__":
    main()
