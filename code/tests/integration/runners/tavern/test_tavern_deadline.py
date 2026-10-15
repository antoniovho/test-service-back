import asyncio
import shutil
import signal
import socket
from collections.abc import Iterator
from types import SimpleNamespace

import pytest

from test_service.infrastructure.adapters.output.runners.tavern.executors import tavern_executor
from test_service.infrastructure.adapters.output.runners.tavern.executors.tavern_executor import (
    TavernExecutor,
)

pytestmark = pytest.mark.skipif(
    shutil.which("tavern-ci") is None, reason="tavern-ci is not available on PATH"
)


@pytest.fixture
def silent_server(monkeypatch) -> Iterator[str]:
    """Listening socket that accepts connections but never answers a request."""
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    yield SimpleNamespace(url=f"http://127.0.0.1:{listener.getsockname()[1]}", listener=listener)
    listener.close()


class TestTavernDeadline:
    async def test_when_deadline_expires_while_tavern_waits_expect_process_killed(
        self, silent_server, monkeypatch
    ) -> None:
        launched = []
        create_subprocess = asyncio.create_subprocess_exec

        async def spy(*args, **kwargs):
            process = await create_subprocess(*args, **kwargs)
            launched.append(process)
            return process

        monkeypatch.setattr(tavern_executor.asyncio, "create_subprocess_exec", spy)
        document = {
            "test_name": "stuck request",
            "stages": [
                {
                    "name": "probe",
                    "request": {"url": f"{silent_server.url}/probe", "method": "GET"},
                    "response": {"status_code": 200},
                }
            ],
        }

        with pytest.raises(TimeoutError):
            async with asyncio.timeout(3):
                await TavernExecutor().execute(document, ("probe",), asyncio.Event())

        assert launched[0].returncode == -signal.SIGKILL

    async def test_when_cancellation_is_requested_during_http_request_expect_process_terminated(
        self, silent_server
    ) -> None:
        cancellation = asyncio.Event()
        document = {
            "test_name": "cancelled request",
            "stages": [
                {
                    "name": "probe",
                    "request": {"url": f"{silent_server.url}/probe", "method": "GET"},
                    "response": {"status_code": 200},
                }
            ],
        }
        execution = asyncio.create_task(
            TavernExecutor().execute(document, ("probe",), cancellation)
        )

        connection, _ = await asyncio.to_thread(silent_server.listener.accept)
        try:
            cancellation.set()
            result = await execution
        finally:
            connection.close()

        assert result.cancelled is True
        assert result.stages == ()
