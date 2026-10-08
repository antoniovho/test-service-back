import asyncio
import json
import stat
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from test_service.infrastructure.adapters.output.runners.tavern.executors import (
    tavern_executor,
)
from test_service.infrastructure.adapters.output.runners.tavern.executors.tavern_executor import (
    TavernExecutor,
    _read_result,
    _reporter_source,
    _terminate_process_group,
    _write_secure,
)


class _Response:
    def __init__(self) -> None:
        self.status_code = 200
        self.headers = {
            "Authorization": "Bearer response-secret",
            "Set-Cookie": "session=response-secret",
            "X-Trace": "trace-value",
        }
        self.text = "response-body"

    def json(self) -> dict[str, str]:
        return {"token": "response-secret"}


class _Process:
    def __init__(self, returncode: int | None = 0) -> None:
        self.pid = 123
        self.returncode = returncode
        self.wait = AsyncMock(return_value=returncode)


class _BlockingProcess:
    def __init__(self) -> None:
        self.pid = 123
        self.returncode: int | None = None
        self.completed = asyncio.Event()

    async def wait(self) -> int:
        await self.completed.wait()
        return self.returncode or 0


class TestTavernExecutor:
    async def test_when_tavern_process_completes_expect_empty_structured_result(
        self, monkeypatch
    ) -> None:
        process = _Process()
        create_subprocess = AsyncMock(return_value=process)

        monkeypatch.setattr(tavern_executor.asyncio, "create_subprocess_exec", create_subprocess)

        result = await TavernExecutor().execute({}, ("request-account",), asyncio.Event())

        assert result.exit_code == 0
        assert result.cancelled is False
        assert result.stages == ()
        create_subprocess.assert_awaited_once()

    async def test_when_tavern_execution_is_cancelled_expect_cancelled_result(
        self, monkeypatch
    ) -> None:
        process = _Process()

        async def wait_for_process(process, cancellation):
            return 143, True

        monkeypatch.setattr(
            tavern_executor.asyncio,
            "create_subprocess_exec",
            AsyncMock(return_value=process),
        )
        monkeypatch.setattr(TavernExecutor, "_wait_for_process", staticmethod(wait_for_process))

        result = await TavernExecutor().execute({}, ("request-account",), asyncio.Event())

        assert result.exit_code == 143
        assert result.cancelled is True
        assert result.stages == ()

    async def test_when_process_finishes_before_cancellation_expect_process_result(self) -> None:
        process = _Process(2)

        exit_code, cancelled = await TavernExecutor._wait_for_process(process, asyncio.Event())

        assert exit_code == 2
        assert cancelled is False

    async def test_when_cancelling_running_process_expect_termination_signal(
        self, monkeypatch
    ) -> None:
        process = _BlockingProcess()
        cancellation = asyncio.Event()
        cancellation.set()
        signals: list[int] = []

        def terminate_process_group(terminated_process, signal):
            signals.append(signal)
            terminated_process.returncode = 143
            terminated_process.completed.set()

        monkeypatch.setattr(tavern_executor, "_terminate_process_group", terminate_process_group)

        exit_code, cancelled = await TavernExecutor._wait_for_process(process, cancellation)

        assert exit_code == 143
        assert cancelled is True
        assert signals == [tavern_executor.signal.SIGTERM]

    def test_when_writing_temporary_file_expect_owner_only_content(self, tmp_path) -> None:
        path = tmp_path / "result.json"

        _write_secure(path, "private-result")

        assert path.read_text(encoding="utf-8") == "private-result"
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    def test_when_reading_structured_result_expect_valid_stages_and_string_variables(
        self, tmp_path
    ) -> None:
        timestamp = datetime(2026, 1, 1, tzinfo=UTC).isoformat()
        result_file = tmp_path / "result.json"
        result_file.write_text(
            json.dumps(
                {
                    "stages": [
                        {
                            "identifier": "request-account",
                            "status": "PASSED",
                            "startedAt": timestamp,
                            "finishedAt": timestamp,
                        }
                    ],
                    "variables": {"sessionId": "123", "ignored": 123},
                }
            ),
            encoding="utf-8",
        )

        result = _read_result(result_file, 0)

        assert result.stages[0].identifier == "request-account"
        assert result.variables == {"sessionId": "123"}

    def test_when_no_result_file_exists_expect_empty_result(self, tmp_path) -> None:
        result = _read_result(tmp_path / "missing.json", 2)

        assert result.exit_code == 2
        assert result.stages == ()

    def test_when_terminating_active_process_expect_group_signal(self, monkeypatch) -> None:
        process = _Process(None)
        signals: list[tuple[int, int]] = []

        monkeypatch.setattr(
            tavern_executor.os,
            "killpg",
            lambda process_id, signal: signals.append((process_id, signal)),
        )

        _terminate_process_group(process, 15)

        assert signals == [(123, 15)]

    def test_when_request_fails_before_response_expect_credentials_redacted(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        namespace["pytest_tavern_beta_before_every_request"](
            {
                "method": "POST",
                "url": "https://api.example.test/accounts",
                "headers": {
                    "Authorization": "Bearer request-secret",
                    "X-Api-Key": "request-secret",
                    "X-Trace": "trace-value",
                },
                "json": {"password": "request-secret"},
            }
        )
        namespace["complete"]("FAILED")

        stage = namespace["result"]["stages"][0]
        request = stage["actual"]["request"]
        serialized = str(stage)

        assert request == {
            "method": "POST",
            "url": "https://api.example.test/accounts",
            "headers": {
                "Authorization": "[REDACTED]",
                "X-Api-Key": "[REDACTED]",
                "X-Trace": "trace-value",
            },
        }
        assert "request-secret" not in serialized

    def test_when_reporter_records_response_expect_sensitive_evidence_redacted(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        namespace["pytest_tavern_beta_before_every_request"]({})
        namespace["pytest_tavern_beta_after_every_response"]({}, _Response())
        namespace["complete"]("PASSED")

        stage = namespace["result"]["stages"][0]
        response = stage["actual"]
        serialized = str(stage)

        assert response["headers"]["Authorization"] == "[REDACTED]"
        assert response["headers"]["Set-Cookie"] == "[REDACTED]"
        assert response["body"] == {"token": "[REDACTED]"}
        assert "response-secret" not in serialized

    def test_when_response_body_exceeds_limit_expect_truncated_evidence(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        evidence = namespace["response_body_evidence"]("x" * 4097)

        assert evidence == {"truncated": True, "content": '"' + "x" * 4095}

    def test_when_tavern_emits_more_requests_than_stages_expect_explicit_runner_error(
        self,
    ) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        namespace["pytest_tavern_beta_before_every_request"]({})

        with pytest.raises(RuntimeError, match="more HTTP requests"):
            namespace["pytest_tavern_beta_before_every_request"]({})
