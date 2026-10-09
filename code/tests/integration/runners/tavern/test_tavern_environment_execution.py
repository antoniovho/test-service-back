import asyncio
import shutil
import socket
from uuid import uuid4

import pytest

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.services.execution.execution_variables_resolver import (
    ExecutionVariablesResolver,
)
from test_service.domain.application.services.execution.secret_redactor import (
    redact_test_case_outcome,
)
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.execution.environment import SecretReference
from test_service.domain.model.execution.execution import ResultStatus
from test_service.infrastructure.adapters.output.runners.tavern.tavern_runner_adapter import (
    TavernRunnerAdapter,
)
from test_service.infrastructure.adapters.output.secrets.environment_secret_resolver import (
    EnvironmentSecretResolver,
)

pytestmark = pytest.mark.skipif(
    shutil.which("tavern-ci") is None, reason="tavern-ci is not available on PATH"
)

_SECRET = "s3cr3t-integration-value"


def _closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class TestEnvironmentExecution:
    async def test_when_environment_provides_url_and_secret_expect_request_sent_with_both(
        self, server
    ) -> None:
        definition = Definition(
            variables={"baseUrl": "https://unused.invalid"},
            actions=(
                Action(
                    "probe",
                    "HTTP",
                    {
                        "url": "{{baseUrl}}/probe",
                        "method": "GET",
                        "headers": {"X-Custom-Token": "{{apiKey}}"},
                    },
                ),
            ),
        )
        environment = {"baseUrl": server.url, "apiKey": SecretReference("env", "API_KEY")}
        resolver = ExecutionVariablesResolver(
            EnvironmentSecretResolver(environ={"TEST_SERVICE_SECRET_API_KEY": _SECRET})
        )
        variables = await resolver.resolve(environment)
        compiled = DefinitionCompiler().compile(uuid4(), definition, variables.values)

        outcome = await TavernRunnerAdapter().execute(compiled, asyncio.Event())
        redacted = redact_test_case_outcome(outcome, variables.secrets)

        assert outcome.status is ResultStatus.PASSED
        assert server.received[0]["x-custom-token"] == _SECRET
        assert _SECRET not in repr(redacted)

    async def test_when_request_fails_before_response_expect_secret_removed_from_outcome(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
        monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
        definition = Definition(
            variables={},
            actions=(
                Action(
                    "probe",
                    "HTTP",
                    {
                        "url": "{{baseUrl}}/probe",
                        "method": "GET",
                        "headers": {"X-Custom-Token": "{{apiKey}}"},
                    },
                ),
            ),
        )
        environment = {
            "baseUrl": f"http://127.0.0.1:{_closed_port()}",
            "apiKey": SecretReference("env", "API_KEY"),
        }
        resolver = ExecutionVariablesResolver(
            EnvironmentSecretResolver(environ={"TEST_SERVICE_SECRET_API_KEY": _SECRET})
        )
        variables = await resolver.resolve(environment)
        compiled = DefinitionCompiler().compile(uuid4(), definition, variables.values)

        outcome = await TavernRunnerAdapter().execute(compiled, asyncio.Event())
        redacted = redact_test_case_outcome(outcome, variables.secrets)

        assert outcome.status is not ResultStatus.PASSED
        assert _SECRET in repr(outcome)
        assert _SECRET not in repr(redacted)
        assert "[REDACTED]" in repr(redacted.actions[0].actual)

    async def test_when_environment_url_is_missing_expect_request_not_sent(self, server) -> None:
        definition = Definition(
            variables={},
            actions=(Action("probe", "HTTP", {"url": "{{baseUrl}}/probe", "method": "GET"}),),
        )
        compiled = DefinitionCompiler().compile(uuid4(), definition)

        outcome = await TavernRunnerAdapter().execute(compiled, asyncio.Event())

        assert outcome.status is not ResultStatus.PASSED
        assert server.received == []
