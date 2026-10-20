import asyncio
import json
import stat
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from tavern._core.exceptions import TestFailError as TavernAssertionError

from test_service.infrastructure.adapters.output.runners.tavern.executors import (
    tavern_executor,
)
from test_service.infrastructure.adapters.output.runners.tavern.executors.tavern_executor import (
    TavernExecutor,
    _read_result,
    _reporter_source,
    _subprocess_environment,
    _tavern_command,
    _terminate_process_group,
    _write_secure,
)


class _Response:
    def __init__(self) -> None:
        self.status_code = 200
        self.headers = {
            "Authorization": "Bearer response-secret",
            "Set-Cookie": "session=response-secret",
            "llm_provider-set-cookie": "session=response-secret",
            "upstream-authorization": "Bearer response-secret",
            "X-Trace": "trace-value",
        }
        self.text = "response-body"

    def json(self) -> dict[str, str]:
        return {"token": "response-secret", "key": "sk-response-secret"}


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
        assert result.variables == {}
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

    async def test_when_launching_tavern_expect_service_secrets_not_inherited(
        self, monkeypatch
    ) -> None:
        create_subprocess = AsyncMock(return_value=_Process())
        monkeypatch.setattr(tavern_executor.asyncio, "create_subprocess_exec", create_subprocess)
        monkeypatch.setenv("DATABASE_PASSWORD", "database-secret")
        monkeypatch.setenv("XRAY_CLIENT_SECRET", "xray-secret")
        monkeypatch.setenv("PATH", "/usr/local/bin:/usr/bin")

        await TavernExecutor().execute({}, ("request-account",), asyncio.Event())

        environment = create_subprocess.await_args.kwargs["env"]
        arguments = create_subprocess.await_args.args
        parameters = create_subprocess.await_args.kwargs
        test_file = Path(arguments[1])

        assert arguments[0] == _tavern_command()
        assert test_file.name == "test-execution.tavern.yaml"
        assert test_file.parent.name.startswith("test-service-")
        assert parameters["cwd"] == test_file.parent
        assert parameters["stdout"] is asyncio.subprocess.DEVNULL
        assert parameters["stderr"] is asyncio.subprocess.DEVNULL
        assert parameters["start_new_session"] is True
        assert environment["PATH"] == "/usr/local/bin:/usr/bin"
        assert "database-secret" not in environment.values()
        assert "xray-secret" not in environment.values()
        assert "DATABASE_PASSWORD" not in environment
        assert "XRAY_CLIENT_SECRET" not in environment

    def test_when_tavern_is_installed_beside_active_interpreter_expect_that_executable_used(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        virtual_environment = tmp_path / "venv" / "bin"
        virtual_environment.mkdir(parents=True)
        interpreter = virtual_environment / "python"
        tavern = virtual_environment / "tavern-ci"
        interpreter.touch()
        tavern.touch(mode=0o755)
        monkeypatch.setattr(tavern_executor.sys, "executable", str(interpreter))

        assert _tavern_command() == str(tavern)

    async def test_when_launching_tavern_expect_expected_temporary_files_written(
        self, monkeypatch
    ) -> None:
        document = {"stages": [{"name": "request-account"}]}
        writes: dict[str, str] = {}
        monkeypatch.setattr(
            tavern_executor,
            "_write_secure",
            lambda path, content: writes.__setitem__(path.name, content),
        )
        monkeypatch.setattr(
            tavern_executor.asyncio,
            "create_subprocess_exec",
            AsyncMock(return_value=_Process()),
        )

        await TavernExecutor().execute(document, ("request-account",), asyncio.Event())

        assert json.loads(writes["test-execution.tavern.yaml"]) == document
        assert 'STAGES = ["request-account"]' in writes["conftest.py"]

    async def test_when_tavern_finishes_expect_report_read_from_standard_result_file(
        self, monkeypatch
    ) -> None:
        process = _Process(7)
        read_paths: list[Path] = []
        expected = tavern_executor.TavernExecutionResult(7, False, (), {})

        def read_result(path: Path, exit_code: int):
            read_paths.append(path)
            assert exit_code == 7
            return expected

        monkeypatch.setattr(
            tavern_executor.asyncio,
            "create_subprocess_exec",
            AsyncMock(return_value=process),
        )
        monkeypatch.setattr(tavern_executor, "_read_result", read_result)

        result = await TavernExecutor().execute({}, (), asyncio.Event())

        assert result is expected
        assert [path.name for path in read_paths] == ["result.json"]

    @pytest.mark.parametrize(
        ("document", "construct"),
        [
            (
                {"stages": [{"request": {"json": {"$ext": {"function": "os:system"}}}}]},
                "$ext",
            ),
            (
                {"stages": [{"request": {"headers": {"X": "{tavern.env_vars.SECRET}"}}}]},
                "tavern",
            ),
        ],
        ids=["ext-directive", "tavern-template-field"],
    )
    async def test_when_document_uses_reserved_construct_expect_error_before_launching_tavern(
        self, monkeypatch, document, construct
    ) -> None:
        create_subprocess = AsyncMock(return_value=_Process())
        monkeypatch.setattr(tavern_executor.asyncio, "create_subprocess_exec", create_subprocess)
        executor = TavernExecutor()
        stage_identifiers = ("request-account",)
        cancellation = asyncio.Event()

        with pytest.raises(ValueError, match="Tavern document uses") as exc:
            await executor.execute(document, stage_identifiers, cancellation)

        assert construct in str(exc.value)
        create_subprocess.assert_not_awaited()

    async def test_when_process_finishes_before_cancellation_expect_process_result(self) -> None:
        process = _Process(2)

        exit_code, cancelled = await TavernExecutor._wait_for_process(process, asyncio.Event())

        assert exit_code == 2
        assert cancelled is False

    async def test_when_process_and_cancellation_complete_together_expect_no_termination(
        self, monkeypatch
    ) -> None:
        process = _Process(2)
        cancellation = asyncio.Event()
        cancellation.set()
        signals: list[int] = []
        monkeypatch.setattr(
            tavern_executor,
            "_terminate_process_group",
            lambda _, signal: signals.append(signal),
        )

        exit_code, cancelled = await TavernExecutor._wait_for_process(process, cancellation)

        assert exit_code == 2
        assert cancelled is False
        assert signals == []

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

    async def test_when_process_does_not_stop_gracefully_expect_forceful_termination(
        self, monkeypatch
    ) -> None:
        process = _BlockingProcess()
        cancellation = asyncio.Event()
        cancellation.set()
        signals: list[int] = []

        def terminate_process_group(terminated_process, signal):
            signals.append(signal)
            if signal == tavern_executor.signal.SIGKILL:
                terminated_process.returncode = -9
                terminated_process.completed.set()

        monkeypatch.setattr(tavern_executor, "_terminate_process_group", terminate_process_group)
        monkeypatch.setattr(
            tavern_executor.asyncio,
            "wait_for",
            AsyncMock(side_effect=TimeoutError),
        )

        exit_code, cancelled = await TavernExecutor._wait_for_process(process, cancellation)

        assert exit_code == -9
        assert cancelled is True
        assert signals == [tavern_executor.signal.SIGTERM, tavern_executor.signal.SIGKILL]

    async def test_when_waiting_task_is_cancelled_expect_process_group_killed(
        self, monkeypatch
    ) -> None:
        process = _BlockingProcess()
        signals: list[int] = []

        def terminate_process_group(terminated_process, signal):
            signals.append(signal)
            terminated_process.returncode = -9
            terminated_process.completed.set()

        monkeypatch.setattr(tavern_executor, "_terminate_process_group", terminate_process_group)
        waiting = asyncio.create_task(TavernExecutor._wait_for_process(process, asyncio.Event()))
        await asyncio.sleep(0)

        waiting.cancel()

        with pytest.raises(asyncio.CancelledError):
            await waiting
        assert signals == [tavern_executor.signal.SIGKILL]

    @pytest.mark.parametrize(
        "name",
        [
            "PATH",
            "LANG",
            "LC_ALL",
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "NO_PROXY",
            "https_proxy",
            "SSL_CERT_FILE",
            "REQUESTS_CA_BUNDLE",
        ],
    )
    def test_when_building_environment_expect_runtime_variable_kept(
        self, monkeypatch, name
    ) -> None:
        monkeypatch.setenv(name, "kept-value")

        environment = _subprocess_environment()

        assert environment[name] == "kept-value"

    @pytest.mark.parametrize(
        "name",
        [
            "DATABASE_PASSWORD",
            "DATABASE_HOST",
            "XRAY_CLIENT_SECRET",
            "JIRA_API_TOKEN",
            "AUTH_JWKS_URL",
            "AWS_SECRET_ACCESS_KEY",
            "PYTEST_ADDOPTS",
        ],
    )
    def test_when_building_environment_expect_other_variable_dropped(
        self, monkeypatch, name
    ) -> None:
        monkeypatch.setenv(name, "dropped-value")

        environment = _subprocess_environment()

        assert name not in environment

    def test_when_writing_temporary_file_expect_owner_only_content(self, tmp_path) -> None:
        path = tmp_path / "result.json"

        _write_secure(path, "private-result")

        assert path.read_text(encoding="utf-8") == "private-result"
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    def test_when_writing_temporary_file_expect_utf8_stream(self, monkeypatch, tmp_path) -> None:
        path = tmp_path / "result.json"
        descriptor = 42
        stream = MagicMock()
        stream.__enter__.return_value = stream
        monkeypatch.setattr(tavern_executor.os, "open", lambda *_: descriptor)
        file_open = MagicMock(return_value=stream)
        monkeypatch.setattr(tavern_executor.os, "fdopen", file_open)

        _write_secure(path, "private-result")

        file_open.assert_called_once_with(descriptor, "w", encoding="utf-8")
        stream.write.assert_called_once_with("private-result")

    def test_when_reading_structured_result_expect_utf8_input(self) -> None:
        timestamp = "2026-01-01T00:00:00+00:00"
        result_file = MagicMock()
        result_file.exists.return_value = True
        result_file.read_text.return_value = json.dumps(
            {
                "stages": [
                    {
                        "identifier": "request-account",
                        "status": "PASSED",
                        "startedAt": timestamp,
                        "finishedAt": timestamp,
                    }
                ],
                "variables": {},
            }
        )

        _read_result(result_file, 0)

        result_file.read_text.assert_called_once_with(encoding="utf-8")

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
                            "expected": {"status_code": 200},
                            "actual": {"statusCode": 200, "body": {"account": "123"}},
                            "errorCode": "NO_ERROR",
                            "errorMessage": "request completed",
                        }
                    ],
                    "variables": {"sessionId": "123", "ignored": 123},
                }
            ),
            encoding="utf-8",
        )

        result = _read_result(result_file, 0)

        assert result.exit_code == 0
        assert result.cancelled is False
        assert result.stages[0].identifier == "request-account"
        assert result.stages[0].status == "PASSED"
        assert result.stages[0].started_at == datetime.fromisoformat(timestamp)
        assert result.stages[0].finished_at == datetime.fromisoformat(timestamp)
        assert result.stages[0].expected == {"status_code": 200}
        assert result.stages[0].actual == {"statusCode": 200, "body": {"account": "123"}}
        assert result.stages[0].error_code == "NO_ERROR"
        assert result.stages[0].error_message == "request completed"
        assert result.variables == {"sessionId": "123"}

    @pytest.mark.parametrize(
        "payload",
        [
            {"stages": [], "variables": []},
            {
                "stages": [
                    {
                        "identifier": "request-account",
                        "status": "SKIPPED",
                        "startedAt": "2026-01-01T00:00:00+00:00",
                        "finishedAt": "2026-01-01T00:00:00+00:00",
                    }
                ],
                "variables": {},
            },
        ],
        ids=["variables-not-object", "unsupported-stage-status"],
    )
    def test_when_reading_report_with_invalid_structure_expect_value_error(
        self, tmp_path, payload
    ) -> None:
        result_file = tmp_path / "result.json"
        result_file.write_text(json.dumps(payload), encoding="utf-8")

        with pytest.raises(ValueError, match="Tavern result report is invalid"):
            _read_result(result_file, 0)

    def test_when_reading_malformed_report_expect_value_error(self, tmp_path) -> None:
        result_file = tmp_path / "result.json"
        result_file.write_text(json.dumps({"stages": [{"status": "PASSED"}]}))

        with pytest.raises(ValueError, match="Tavern result report is invalid"):
            _read_result(result_file, 0)

    def test_when_reading_invalid_json_report_expect_value_error(self, tmp_path) -> None:
        result_file = tmp_path / "result.json"
        result_file.write_text("not-json", encoding="utf-8")

        with pytest.raises(ValueError, match="Tavern result report is invalid"):
            _read_result(result_file, 0)

    def test_when_no_result_file_exists_expect_empty_result(self, tmp_path) -> None:
        result = _read_result(tmp_path / "missing.json", 2)

        assert result.exit_code == 2
        assert result.cancelled is False
        assert result.stages == ()
        assert result.variables == {}

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

    def test_when_terminating_completed_process_expect_no_signal(self, monkeypatch) -> None:
        process = _Process(0)
        signals: list[tuple[int, int]] = []
        monkeypatch.setattr(
            tavern_executor.os,
            "killpg",
            lambda process_id, signal: signals.append((process_id, signal)),
        )

        _terminate_process_group(process, 15)

        assert signals == []

    def test_when_request_fails_before_response_expect_credentials_redacted(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        namespace["pytest_tavern_beta_before_every_request"](
            {
                "method": "POST",
                "url": "https://api.example.test/accounts?access_token=url-secret&page=2",
                "headers": {
                    "Authorization": "Bearer request-secret",
                    "X-Api-Key": "request-secret",
                    "X-Trace": "trace-value",
                },
                "params": {"key": "request-secret", "page": 1},
                "json": {"password": "request-secret"},
            }
        )
        namespace["complete"]("FAILED")

        stage = namespace["result"]["stages"][0]
        request = stage["actual"]["request"]
        serialized = str(stage)

        assert request == {
            "method": "POST",
            "url": "https://api.example.test/accounts?access_token=%5BREDACTED%5D&page=2",
            "headers": {
                "Authorization": "[REDACTED]",
                "X-Api-Key": "[REDACTED]",
                "X-Trace": "trace-value",
            },
            "params": {"key": "[REDACTED]", "page": 1},
        }
        assert "request-secret" not in serialized
        assert "url-secret" not in serialized

    def test_when_reporter_records_tavern_assertion_expect_failed_with_redacted_error(
        self,
    ) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)
        namespace["pytest_tavern_beta_before_every_request"]({})
        call = SimpleNamespace(
            when="call",
            excinfo=SimpleNamespace(
                value=TavernAssertionError('HTTP 400: {"access_token": "response-secret"}')
            ),
        )

        namespace["pytest_runtest_makereport"](None, call)

        stage = namespace["result"]["stages"][0]
        assert stage["status"] == "FAILED"
        assert stage["errorCode"] == "TAVERN_ASSERTION_FAILED"
        assert "response-secret" not in stage["errorMessage"]

    def test_when_reporter_error_has_no_text_expect_exception_type_recorded(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)
        namespace["pytest_tavern_beta_before_every_request"]({})
        call = SimpleNamespace(when="call", excinfo=SimpleNamespace(value=RuntimeError()))

        namespace["pytest_runtest_makereport"](None, call)

        stage = namespace["result"]["stages"][0]
        assert stage["status"] == "ERROR"
        assert stage["errorCode"] == "TAVERN_EXECUTION_ERROR"
        assert stage["errorMessage"] == "RuntimeError"

    @pytest.mark.parametrize(
        ("technical_detail", "expected_code", "expected_message"),
        [
            (
                "SSLError: SSL connection timeout; api_key=transport-secret",
                "TAVERN_TLS_HANDSHAKE_TIMEOUT",
                "HTTP request timed out while establishing the TLS connection; "
                "no response was received.",
            ),
            (
                "SSLError: certificate verify failed: self signed certificate",
                "TAVERN_TLS_CERTIFICATE_ERROR",
                "TLS certificate verification failed before an HTTP response was received.",
            ),
            (
                "ConnectTimeout: failed to establish a new connection",
                "TAVERN_CONNECT_TIMEOUT",
                "HTTP request timed out while connecting to the target; no response was received.",
            ),
            (
                "ReadTimeout: HTTPSConnectionPool read timed out",
                "TAVERN_READ_TIMEOUT",
                "HTTP connection was established but no response was received before the timeout.",
            ),
            (
                "ConnectionError: connection refused",
                "TAVERN_CONNECTION_ERROR",
                "HTTP connection failed before a response was received.",
            ),
        ],
    )
    def test_when_reporter_detects_transport_failure_expect_safe_category(
        self, technical_detail, expected_code, expected_message
    ) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)
        namespace["pytest_tavern_beta_before_every_request"]({})
        error = RuntimeError("RestRequestException")
        error.__cause__ = RuntimeError(technical_detail)
        call = SimpleNamespace(
            when="call",
            excinfo=SimpleNamespace(
                value=error,
                getrepr=lambda **_: f"Traceback containing {technical_detail}",
            ),
        )

        namespace["pytest_runtest_makereport"](None, call)

        stage = namespace["result"]["stages"][0]
        assert stage["status"] == "ERROR"
        assert stage["errorCode"] == expected_code
        assert stage["errorMessage"] == expected_message
        assert "transport-secret" not in str(stage)
        assert "diagnosticTrace" in stage
        assert "Traceback containing" in stage["diagnosticTrace"]

    def test_when_trace_contains_token_hash_expect_hash_redacted(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)
        namespace["pytest_tavern_beta_before_every_request"]({})
        error = RuntimeError(
            "Key Hash (Token) =6b9c111bd578697f9aa5eff59014567da19a193b0f022a08c65b1470bec16903"
        )
        call = SimpleNamespace(
            when="call",
            excinfo=SimpleNamespace(
                value=error,
                getrepr=lambda **_: f"Traceback containing {error}",
            ),
        )

        namespace["pytest_runtest_makereport"](None, call)

        trace = namespace["result"]["stages"][0]["diagnosticTrace"]
        assert "6b9c111bd578697f9aa5eff59014567da19a193b0f022a08c65b1470bec16903" not in trace
        assert "Key Hash (Token) =[REDACTED]" in trace

    def test_when_reporter_error_includes_traceback_expect_only_actionable_summary(
        self,
    ) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)
        namespace["pytest_tavern_beta_before_every_request"]({})
        message = (
            "Response header mismatch\n"
            "- Error calling validate function '<function validate at 0xdeadbeef>':\n"
            "    Traceback (most recent call last):\n"
            '      File "/home/user/private/project.py", line 1, in validate'
        )
        call = SimpleNamespace(
            when="call", excinfo=SimpleNamespace(value=TavernAssertionError(message))
        )

        namespace["pytest_runtest_makereport"](None, call)

        error_message = namespace["result"]["stages"][0]["errorMessage"]
        assert error_message == (
            "Response header mismatch\n- Error calling validate function '<function validate>':"
        )
        assert "Traceback" not in error_message
        assert "/home/" not in error_message
        assert "0x" not in error_message

    def test_when_reporter_records_technical_error_expect_error_and_truncated_message(
        self,
    ) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)
        namespace["pytest_tavern_beta_before_every_request"]({})
        message = 'HTTP 500: {"token": "response-secret"} ' + "x" * 2000
        call = SimpleNamespace(when="call", excinfo=SimpleNamespace(value=RuntimeError(message)))

        namespace["pytest_runtest_makereport"](None, call)

        stage = namespace["result"]["stages"][0]
        assert stage["status"] == "ERROR"
        assert stage["errorCode"] == "TAVERN_EXECUTION_ERROR"
        assert len(stage["errorMessage"]) <= 1024
        assert "response-secret" not in stage["errorMessage"]

    def test_when_reporter_records_response_expect_sensitive_evidence_redacted(self) -> None:
        namespace: dict[str, object] = {}
        exec(_reporter_source(("request-account",)), namespace)

        namespace["pytest_tavern_beta_before_every_request"]({})
        namespace["pytest_tavern_beta_after_every_response"](
            {"verify_response_with": {"forbiddenText": "response-secret"}}, _Response()
        )
        namespace["complete"]("PASSED")

        stage = namespace["result"]["stages"][0]
        response = stage["actual"]
        serialized = str(stage)

        assert response["headers"]["Authorization"] == "[REDACTED]"
        assert response["headers"]["Set-Cookie"] == "[REDACTED]"
        assert response["headers"]["llm_provider-set-cookie"] == "[REDACTED]"
        assert response["headers"]["upstream-authorization"] == "[REDACTED]"
        assert response["body"] == {"token": "[REDACTED]", "key": "[REDACTED]"}
        assert stage["expected"]["verify_response_with"]["forbiddenText"] == "[REDACTED]"
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
