"""Isolated Tavern subprocess execution and structured pytest reporting."""

import asyncio
import json
import os
import signal
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from test_service.infrastructure.adapters.output.runners.tavern.dtos.tavern_dtos import (
    TavernExecutionResult,
    TavernStageResult,
)


class TavernExecutor:
    """Execute Tavern documents in isolated subprocess groups.

    A temporary working directory holds the Tavern document, its reporting
    plugin, and the resulting structured execution report.
    """

    async def execute(
        self,
        document: Mapping[str, object],
        stage_identifiers: tuple[str, ...],
        cancellation: asyncio.Event,
    ) -> TavernExecutionResult:
        """Execute a Tavern document and collect its structured result.

        Args:
            document: Tavern test document to serialize into the temporary
                execution directory.
            stage_identifiers: Ordered domain action identifiers, used by the
                temporary pytest reporter to associate Tavern stages with
                their source actions.
            cancellation: Event that requests termination of the Tavern
                process group.

        Returns:
            Normalized result containing the process exit code, cancellation
            state, stage outcomes, and Tavern variables saved during execution.

        Raises:
            OSError: If the temporary files cannot be created or the Tavern
                process cannot be started.
        """
        with tempfile.TemporaryDirectory(prefix="test-service-") as directory:
            root = Path(directory)
            test_file = root / "test-execution.tavern.yaml"
            result_file = root / "result.json"
            _write_secure(test_file, json.dumps(document))
            _write_secure(root / "conftest.py", _reporter_source(stage_identifiers))

            # Execute the Tavern test document in a subprocess using tavern-ci
            process = await asyncio.create_subprocess_exec(
                "tavern-ci",
                str(test_file),
                cwd=root,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True,
            )
            exit_code, cancelled = await self._wait_for_process(process, cancellation)
            if cancelled:
                return TavernExecutionResult(exit_code, True, (), {})
            return _read_result(result_file, exit_code)

    @staticmethod
    async def _wait_for_process(
        process: asyncio.subprocess.Process, cancellation: asyncio.Event
    ) -> tuple[int, bool]:
        """Wait for Tavern or terminate its process group after cancellation.

        Args:
            process: Active Tavern subprocess, started in its own process
                group.
            cancellation: Event that requests graceful process termination.

        Returns:
            A pair containing the process exit code and whether cancellation
            caused termination.
        """
        process_wait = asyncio.create_task(process.wait())
        cancellation_wait = asyncio.create_task(cancellation.wait())
        try:
            done, _ = await asyncio.wait(
                {process_wait, cancellation_wait}, return_when=asyncio.FIRST_COMPLETED
            )
            if cancellation_wait in done and not process_wait.done():
                _terminate_process_group(process, signal.SIGTERM)
                try:
                    await asyncio.wait_for(process_wait, timeout=3)
                except TimeoutError:
                    _terminate_process_group(process, signal.SIGKILL)
                    await process_wait
                return process.returncode if process.returncode is not None else 130, True
            return process.returncode if process.returncode is not None else 0, False
        finally:
            if not cancellation_wait.done():
                cancellation_wait.cancel()
            await asyncio.gather(cancellation_wait, return_exceptions=True)


def _write_secure(path: Path, content: str) -> None:
    """Write content to a temporary file with owner-only permissions.

    Args:
        path: Target file path in the temporary execution directory.
        content: UTF-8 text to write.

    Raises:
        OSError: If the file cannot be created or written.
    """
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(content)


def _read_result(result_file: Path, exit_code: int) -> TavernExecutionResult:
    """Deserialize the result emitted by the temporary pytest plugin.

    Args:
        result_file: Expected location of the JSON report emitted by pytest.
        exit_code: Exit code returned by the Tavern subprocess.

    Returns:
        Execution result populated from the report, or an empty, non-cancelled
        result when the reporter did not create one.

    Raises:
        json.JSONDecodeError: If the generated report is not valid JSON.
    """
    if not result_file.exists():
        return TavernExecutionResult(exit_code, False, (), {})
    payload = json.loads(result_file.read_text(encoding="utf-8"))
    stages = tuple(
        TavernStageResult(
            identifier=item["identifier"],
            status=item["status"],
            started_at=datetime.fromisoformat(item["startedAt"]),
            finished_at=datetime.fromisoformat(item["finishedAt"]),
            expected=item.get("expected"),
            actual=item.get("actual"),
            error_code=item.get("errorCode"),
            error_message=item.get("errorMessage"),
        )
        for item in payload.get("stages", [])
    )
    variables = {
        key: value
        for key, value in payload.get("variables", {}).items()
        if isinstance(key, str) and isinstance(value, str)
    }
    return TavernExecutionResult(exit_code, False, stages, variables)


def _terminate_process_group(process: asyncio.subprocess.Process, signal_value: int) -> None:
    """Send a signal to Tavern and every process in its isolated group.

    Args:
        process: Tavern subprocess whose process group receives the signal.
        signal_value: POSIX signal to send to the group.
    """
    if process.returncode is None:
        os.killpg(process.pid, signal_value)


def _reporter_source(stage_identifiers: tuple[str, ...]) -> str:
    """Generate the pytest plugin that writes structured Tavern stage results.

    Args:
        stage_identifiers: Ordered domain action identifiers for the current
            Tavern execution block.

    Returns:
        Python source for a temporary pytest plugin that persists stage
        outcomes and newly saved string variables to ``result.json``.
    """
    return f'''import json
from datetime import UTC, datetime
from tavern._core.exceptions import TestFailError

STAGES = {json.dumps(stage_identifiers)}
result = {{"stages": [], "variables": {{}}}}
initial_variables = set()
next_stage = 0
pending = None

def now():
    """Return the current UTC instant in JSON-compatible form."""
    return datetime.now(UTC).isoformat()

def safe(value):
    """Convert values that may occur in Tavern hooks into JSON-safe data."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)

def complete(status, code=None, message=None):
    """Persist the pending stage with its terminal structured status."""
    global pending
    if pending is None:
        return
    pending["status"] = status
    pending["finishedAt"] = now()
    if code:
        pending["errorCode"] = code
    if message:
        pending["errorMessage"] = message
    result["stages"].append(pending)
    pending = None

def pytest_tavern_beta_before_every_test_run(test_dict, variables):
    """Capture variables that existed before the multi-stage block started."""
    global initial_variables
    initial_variables = set(variables)

def pytest_tavern_beta_before_every_request(request_args):
    """Open the structured result record for the next HTTP stage."""
    global next_stage, pending
    complete("PASSED")
    pending = {{"identifier": STAGES[next_stage], "startedAt": now(),
               "actual": {{"request": safe(dict(request_args))}}}}
    next_stage += 1

def pytest_tavern_beta_after_every_response(expected, response):
    """Record the expected and received response before Tavern verifies it."""
    if pending is None:
        return
    try:
        body = response.json()
    except ValueError:
        body = response.text
    pending["expected"] = safe(expected)
    pending["actual"] = {{"statusCode": response.status_code,
                         "headers": safe(dict(response.headers)), "body": safe(body)}}

def pytest_tavern_beta_after_every_test_run(test_dict, variables):
    """Expose serializable variables saved by Tavern for a later HTTP block."""
    result["variables"] = {{key: value for key, value in variables.items()
                           if key not in initial_variables and isinstance(key, str)
                           and isinstance(value, str)}}

def pytest_runtest_makereport(item, call):
    """Complete the current stage from pytest's structured execution report."""
    global pending
    if call.when != "call":
        return
    if call.excinfo is None:
        complete("PASSED")
        return
    error = call.excinfo.value
    stage = getattr(error, "stage", {{}})
    identifier = stage.get("name") if isinstance(stage, dict) else None
    if pending is None and identifier:
        pending = {{"identifier": identifier, "startedAt": now()}}
    if pending is not None:
        code = ("TAVERN_ASSERTION_FAILED" if isinstance(error, TestFailError)
                else "TAVERN_EXECUTION_ERROR")
        complete("FAILED", code, str(error))

def pytest_sessionfinish(session, exitstatus):
    """Write the final structured result for the parent Tavern executor."""
    (session.config.rootpath / "result.json").write_text(
        json.dumps(result), encoding="utf-8"
    )
'''
