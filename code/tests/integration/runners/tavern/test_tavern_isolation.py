import asyncio
import shutil

import pytest

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import CompiledAction, CompiledTestCase
from test_service.infrastructure.adapters.output.runners.tavern.executors import tavern_executor
from test_service.infrastructure.adapters.output.runners.tavern.executors.tavern_executor import (
    TavernExecutor,
)
from test_service.infrastructure.adapters.output.runners.tavern.tavern_runner_adapter import (
    TavernRunnerAdapter,
)

pytestmark = pytest.mark.skipif(
    shutil.which("tavern-ci") is None, reason="tavern-ci is not available on PATH"
)

_SENTINEL_NAME = "TEST_SERVICE_LEAK_SENTINEL"
_SENTINEL_VALUE = "sentinel-secret-value"


class TestTavernIsolation:
    async def test_when_document_sends_plain_header_expect_request_received_and_stage_passed(
        self, server
    ) -> None:
        document = _document(server.url, {"X-Probe": "hello"})

        result = await TavernExecutor().execute(document, ("probe",), asyncio.Event())

        assert result.exit_code == 0
        assert result.stages[0].status == "PASSED"
        assert server.received[0]["x-probe"] == "hello"

    async def test_when_document_references_service_secret_expect_rejected_and_nothing_sent(
        self, server, monkeypatch
    ) -> None:
        monkeypatch.setenv(_SENTINEL_NAME, _SENTINEL_VALUE)
        document = _document(server.url, {"X-Leak": f"{{tavern.env_vars.{_SENTINEL_NAME}}}"})

        with pytest.raises(ValueError, match="template field"):
            await TavernExecutor().execute(document, ("probe",), asyncio.Event())

        assert server.received == []

    async def test_when_reserved_construct_guard_is_bypassed_expect_secret_still_not_sent(
        self, server, monkeypatch
    ) -> None:
        monkeypatch.setenv(_SENTINEL_NAME, _SENTINEL_VALUE)
        monkeypatch.setattr(tavern_executor, "find_reserved_construct", lambda document: None)
        document = _document(server.url, {"X-Leak": f"{{tavern.env_vars.{_SENTINEL_NAME}}}"})

        await TavernExecutor().execute(document, ("probe",), asyncio.Event())

        assert all(_SENTINEL_VALUE not in str(request) for request in server.received)

    async def test_when_variable_value_looks_like_secret_reference_expect_literal_text_sent(
        self, server, monkeypatch
    ) -> None:
        monkeypatch.setenv(_SENTINEL_NAME, _SENTINEL_VALUE)
        reference = f"{{tavern.env_vars.{_SENTINEL_NAME}}}"
        action = CompiledAction(
            "probe", "HTTP", 0, {"url": f"{server.url}/probe", "headers": {"X-Token": "{{token}}"}}
        )
        test_case = CompiledTestCase("case-id", {"token": reference}, (action,))

        outcome = await TavernRunnerAdapter().execute(test_case, asyncio.Event())

        assert outcome.status is ResultStatus.PASSED
        assert server.received[0]["x-token"] == reference

    async def test_when_document_with_ext_directive_reaches_executor_expect_nothing_executed(
        self, server, tmp_path
    ) -> None:
        marker = tmp_path / "executed"
        document = _document(server.url, {})
        document["stages"][0]["request"]["json"] = {
            "$ext": {"function": "os:system", "extra_args": [f"touch {marker}"]}
        }

        with pytest.raises(ValueError, match="executable directive"):
            await TavernExecutor().execute(document, ("probe",), asyncio.Event())

        assert not marker.exists()
        assert server.received == []

    async def test_when_configuration_uses_ext_directive_expect_nothing_executed(
        self, server, tmp_path
    ) -> None:
        marker = tmp_path / "executed"
        action = CompiledAction(
            "probe",
            "HTTP",
            0,
            {
                "url": f"{server.url}/probe",
                "json": {"$ext": {"function": "os:system", "extra_args": [f"touch {marker}"]}},
            },
        )
        test_case = CompiledTestCase("case-id", {}, (action,))

        outcome = await TavernRunnerAdapter().execute(test_case, asyncio.Event())

        assert outcome.status is not ResultStatus.PASSED
        assert outcome.error_code == "TAVERN_RUNNER_ERROR"
        assert not marker.exists()
        assert server.received == []


def _document(url: str, headers: dict[str, str]) -> dict[str, object]:
    return {
        "test_name": "isolation probe",
        "stages": [
            {
                "name": "probe",
                "request": {"url": f"{url}/probe", "method": "GET", "headers": headers},
                "response": {"status_code": 200},
            }
        ],
    }
