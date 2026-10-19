"""Isolated Tavern subprocess execution and structured pytest reporting."""

import asyncio
import json
import os
import signal
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from test_service.infrastructure.adapters.output.runners.tavern.dtos.tavern_dtos import (
    TavernExecutionResult,
    TavernStageResult,
)
from test_service.infrastructure.adapters.output.runners.tavern.tavern_exceptions import (
    TavernResultInvalidError,
)
from test_service.infrastructure.adapters.output.runners.tavern.tavern_safety import (
    find_unsafe_tavern_construct,
)

# Tavern exposes the whole process environment to test documents, so only what the
# subprocess needs to start and reach targets through proxies is passed on.
_INHERITED_ENVIRONMENT = frozenset(
    {
        "PATH",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "no_proxy",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
    }
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
            ValueError: If the document uses a construct Tavern would evaluate
                as code or as privileged data.
            OSError: If the temporary files cannot be created or the Tavern
                process cannot be started.
        """
        unsafe = find_unsafe_tavern_construct(document)
        if unsafe is not None:
            raise ValueError(f"Tavern document uses {unsafe}")
        with tempfile.TemporaryDirectory(prefix="test-service-") as directory:
            root = Path(directory)
            test_file = root / "test-execution.tavern.yaml"
            result_file = root / "result.json"
            _write_secure(test_file, json.dumps(document))
            _write_secure(root / "conftest.py", _reporter_source(stage_identifiers))

            # Execute the Tavern test document in a subprocess using tavern-ci
            process = await asyncio.create_subprocess_exec(
                _tavern_command(),
                str(test_file),
                cwd=root,
                env=_subprocess_environment(),
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

        Raises:
            asyncio.CancelledError: If the awaiting task is cancelled; the process
                group is killed first.
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
        except asyncio.CancelledError:
            # The caller's deadline or a shutdown stopped us: no Tavern group may outlive it.
            _terminate_process_group(process, signal.SIGKILL)
            await process_wait
            raise
        finally:
            if not cancellation_wait.done():
                cancellation_wait.cancel()
            await asyncio.gather(cancellation_wait, return_exceptions=True)


def _tavern_command() -> str:
    """Resolve Tavern from the active virtual environment before consulting ``PATH``.

    Application launchers such as VS Code invoke the virtual-environment
    interpreter directly but do not necessarily prepend its ``bin`` directory
    to ``PATH``. Tavern is installed beside that interpreter, so prefer that
    executable and retain the bare command for system installations.
    """
    executable_name = "tavern-ci.exe" if os.name == "nt" else "tavern-ci"
    candidate = Path(sys.executable).with_name(executable_name)
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return executable_name


def _subprocess_environment() -> dict[str, str]:
    """Build the minimal environment handed to the Tavern subprocess.

    Returns:
        Only the allow-listed variables currently set in this process, so service
        credentials such as database or integration secrets never reach Tavern.
    """
    return {name: value for name, value in os.environ.items() if name in _INHERITED_ENVIRONMENT}


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
        TavernResultInvalidError: If the generated report is malformed or incomplete.
    """
    if not result_file.exists():
        return TavernExecutionResult(exit_code, False, (), {})
    try:
        payload = json.loads(result_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError
        raw_stages = payload["stages"]
        raw_variables = payload["variables"]
        if not isinstance(raw_stages, list) or not isinstance(raw_variables, dict):
            raise TypeError
        stages_list = []
        for item in raw_stages:
            if not isinstance(item, dict):
                raise TypeError
            identifier = item["identifier"]
            status = item["status"]
            started_at = item["startedAt"]
            finished_at = item["finishedAt"]
            if (
                not isinstance(identifier, str)
                or status not in {"PASSED", "FAILED", "ERROR"}
                or not isinstance(started_at, str)
                or not isinstance(finished_at, str)
            ):
                raise TypeError
            stages_list.append(
                TavernStageResult(
                    identifier=identifier,
                    status=status,
                    started_at=datetime.fromisoformat(started_at),
                    finished_at=datetime.fromisoformat(finished_at),
                    expected=item.get("expected"),
                    actual=item.get("actual"),
                    error_code=item.get("errorCode"),
                    error_message=item.get("errorMessage"),
                )
            )
        stages = tuple(stages_list)
        variables = {
            key: value
            for key, value in raw_variables.items()
            if isinstance(key, str) and isinstance(value, str)
        }
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise TavernResultInvalidError("Tavern result report is invalid") from exc
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
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import re

STAGES = {json.dumps(stage_identifiers)}
result = {{"stages": [], "variables": {{}}}}
initial_variables = set()
next_stage = 0
pending = None
SENSITIVE_HEADERS = frozenset({{
    "authorization", "cookie", "proxy-authorization", "set-cookie", "x-api-key",
}})
SENSITIVE_FIELDS = frozenset({{
    "access_token", "api_key", "authorization", "key", "password",
    "forbiddentext", "refresh_token", "secret", "token",
}})
NORMALIZED_SENSITIVE_FIELDS = frozenset(
    re.sub(r"[^a-z0-9]", "", field.lower()) for field in SENSITIVE_FIELDS
)
MAX_RESPONSE_BODY_CHARS = 4096
MAX_ERROR_MESSAGE_CHARS = 1024

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

def redact_headers(headers):
    """Remove credentials from HTTP headers before recording execution evidence."""
    return {{key: "[REDACTED]" if key.lower() in SENSITIVE_HEADERS else value
            for key, value in headers.items()}}

def is_sensitive_field(key):
    """Match common credential names regardless of case or separators."""
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in NORMALIZED_SENSITIVE_FIELDS

def redact_url(url):
    """Redact common credential values in request query parameters."""
    try:
        parts = urlsplit(url)
        query = urlencode([
            (key, "[REDACTED]" if is_sensitive_field(key) else value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
        ])
        netloc = parts.netloc
        if "@" in netloc:
            netloc = "[REDACTED]@" + netloc.rsplit("@", 1)[1]
        return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment))
    except (TypeError, ValueError):
        return "[REDACTED]"

def request_evidence(request_args):
    """Keep request metadata without retaining potentially sensitive request bodies."""
    return {{key: safe(redact_fields(request_args[key]))
            if key == "params" else redact_url(request_args[key])
            if key == "url" else safe(request_args[key])
            for key in ("method", "url", "params") if key in request_args}} | {{
                "headers": redact_headers(request_args.get("headers", {{}}))
            }}

def redact_fields(value):
    """Remove common credential fields from nested JSON-compatible response bodies."""
    return (
        {{key: "[REDACTED]" if is_sensitive_field(key) else redact_fields(item)
          for key, item in value.items()}}
        if isinstance(value, dict)
        else [redact_fields(item) for item in value]
        if isinstance(value, list)
        else value
    )

def response_body_evidence(body):
    """Limit response-body size before persisting it as execution evidence."""
    redacted_body = redact_fields(body)
    serialized = json.dumps(redacted_body, default=repr)
    if len(serialized) <= MAX_RESPONSE_BODY_CHARS:
        return safe(redacted_body)
    return {{"truncated": True, "content": serialized[:MAX_RESPONSE_BODY_CHARS]}}

def redact_error_message(message):
    """Redact credentials and implementation details from persisted error evidence."""
    text = str(message) or type(message).__name__
    text = text.split("Traceback (most recent call last):", maxsplit=1)[0].rstrip()
    text = re.sub(r' at 0x[0-9a-fA-F]+', '', text)
    for field in SENSITIVE_FIELDS:
        pattern = re.compile(
            r'((?:"|\\')?' + re.escape(field) + r'(?:(?:"|\\'))?\\s*[:=]\\s*)'
            r'(?:(?:"(?:\\\\.|[^"\\\\])*"|\\'(?:\\\\.|[^\\'\\\\])*\\')|[^,\\s]+)',
            re.IGNORECASE,
        )
        text = pattern.sub(r'\\1"[REDACTED]"', text)
    return text[:MAX_ERROR_MESSAGE_CHARS]

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
    if next_stage >= len(STAGES):
        raise RuntimeError("Tavern emitted more HTTP requests than configured stages")
    pending = {{"identifier": STAGES[next_stage], "startedAt": now(),
               "actual": {{"request": request_evidence(request_args)}}}}
    next_stage += 1

def pytest_tavern_beta_after_every_response(expected, response):
    """Record the expected and received response before Tavern verifies it."""
    if pending is None:
        return
    try:
        body = response.json()
    except ValueError:
        body = response.text
    pending["expected"] = safe(redact_fields(expected))
    pending["actual"] = {{"statusCode": response.status_code,
                         "headers": redact_headers(response.headers),
                         "body": response_body_evidence(body)}}

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
        assertion_failed = isinstance(error, TestFailError)
        code = "TAVERN_ASSERTION_FAILED" if assertion_failed else "TAVERN_EXECUTION_ERROR"
        status = "FAILED" if assertion_failed else "ERROR"
        complete(status, code, redact_error_message(error))

def pytest_sessionfinish(session, exitstatus):
    """Write the final structured result for the parent Tavern executor."""
    (session.config.rootpath / "result.json").write_text(
        json.dumps(result), encoding="utf-8"
    )
'''
