import argparse
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from test_service.import_corpus import _importer, _parser, main, run_import
from test_service.infrastructure.adapters.input.cli.corpus_importer import ImportReport


class TestImportCorpusCommand:
    def test_when_importer_is_built_expect_required_dependencies_injected(self) -> None:
        injector = Mock()

        with patch("test_service.import_corpus.get_injector", return_value=injector):
            _importer()

        assert injector.inject.call_count == 4

    def test_when_selecting_two_files_expect_them_parsed_in_order(self) -> None:
        arguments = _parser().parse_args(
            [
                "--project-key",
                "KAN",
                "--requested-by",
                "corpus-import",
                "--file",
                "precondition.json",
                "--file",
                "test-case.json",
                "--dry-run",
            ]
        )

        assert arguments.directory is None
        assert arguments.files == [Path("precondition.json"), Path("test-case.json")]
        assert arguments.dry_run is True

    async def test_when_files_are_selected_expect_selected_import_and_database_disposal(
        self,
    ) -> None:
        arguments = argparse.Namespace(
            directory=None,
            files=[Path("precondition.json"), Path("test-case.json")],
            project_key="KAN",
            requested_by="corpus-import",
            dry_run=True,
        )
        importer = Mock()
        importer.import_files = AsyncMock(return_value=ImportReport(created_test_cases=1))
        database = Mock()
        database.dispose = AsyncMock()
        injector = Mock()
        injector.inject.return_value = database

        with (
            patch("test_service.import_corpus.get_injector", return_value=injector),
            patch("test_service.import_corpus._importer", return_value=importer),
        ):
            report = await run_import(arguments)

        assert report.created_test_cases == 1
        importer.import_files.assert_awaited_once_with(
            arguments.files, "KAN", "corpus-import", True
        )
        database.dispose.assert_awaited_once()

    def test_when_import_succeeds_expect_json_report_written(self, capsys) -> None:
        def return_report(coroutine):
            coroutine.close()
            return ImportReport(created_preconditions=1, created_test_cases=1)

        with patch(
            "test_service.import_corpus.asyncio.run",
            side_effect=return_report,
        ):
            main(
                [
                    "--project-key",
                    "KAN",
                    "--requested-by",
                    "corpus-import",
                    "--file",
                    "test-case.json",
                ]
            )

        assert capsys.readouterr().out == (
            '{"created_preconditions": 1, "created_test_cases": 1, '
            '"skipped_preconditions": 0, "skipped_test_cases": 0}\n'
        )

    def test_when_import_fails_expect_argument_error(self) -> None:
        def raise_import_error(coroutine):
            coroutine.close()
            raise ValueError("bad corpus")

        with patch("test_service.import_corpus.asyncio.run", side_effect=raise_import_error):
            with pytest.raises(SystemExit):
                main(
                    [
                        "--project-key",
                        "KAN",
                        "--requested-by",
                        "corpus-import",
                        "--file",
                        "test-case.json",
                    ]
                )

    async def test_when_directory_is_selected_expect_all_its_documents_imported(self) -> None:
        arguments = argparse.Namespace(
            directory=Path("data"),
            files=None,
            project_key="KAN",
            requested_by="corpus-import",
            dry_run=False,
        )
        importer = Mock()
        importer.import_directory = AsyncMock(return_value=ImportReport())
        database = Mock()
        database.dispose = AsyncMock()
        injector = Mock()
        injector.inject.return_value = database

        with (
            patch("test_service.import_corpus.get_injector", return_value=injector),
            patch("test_service.import_corpus._importer", return_value=importer),
        ):
            await run_import(arguments)

        importer.import_directory.assert_awaited_once_with(
            Path("data"), "KAN", "corpus-import", False
        )
