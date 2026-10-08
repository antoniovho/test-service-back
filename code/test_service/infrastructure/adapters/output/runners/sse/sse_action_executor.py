"""SSE action execution for runner adapters."""

import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime

import httpx

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledAction,
    RunnerActionOutcome,
)
from test_service.infrastructure.adapters.output.runners.tavern.variable_renderer import (
    render_service_variables,
)


class SseExecutor:
    """Execute one bounded server-sent events action over a shared HTTP client."""

    async def execute(
        self,
        client: httpx.AsyncClient,
        action: CompiledAction,
        context: Mapping[str, str],
        cancellation: asyncio.Event,
    ) -> RunnerActionOutcome:
        """Execute an SSE action and normalize its outcome.

        Args:
            client: HTTP client owned by the runner orchestration layer.
            action: Validated SSE action to execute.
            context: Service and previously saved Tavern variables used to
                render the action configuration.
            cancellation: Event that stops stream consumption promptly.

        Returns:
            Normalized action outcome containing received events or failure
            details.
        """
        started_at = datetime.now(UTC)
        events: list[dict[str, str]] = []
        try:
            config = render_service_variables(action.configuration, context)
            if not isinstance(config, dict):
                raise ValueError("SSE action configuration must be an object")
            url = config.get("url")
            if not isinstance(url, str) or not url:
                raise ValueError("SSE action configuration must define a non-empty url")
            timeout = float(config.get("receiveTimeoutSeconds", 30))
            max_events = int(config.get("maxEvents", 1))
            async with client.stream(
                "GET", url, headers=config.get("headers"), timeout=timeout
            ) as response:
                response.raise_for_status()
                events, cancelled = await self._read_events(response, max_events, cancellation)
            if cancelled:
                return RunnerActionOutcome(
                    action.identifier,
                    action.action_type,
                    ResultStatus.SKIPPED,
                    started_at,
                    datetime.now(UTC),
                    actual={"events": events},
                    error_code="CANCELLED",
                    error_message="SSE stream cancelled",
                )
            expected_event = config.get("expectedEvent")
            if expected_event and not any(item.get("event") == expected_event for item in events):
                return self._failed(
                    action, started_at, "SSE_EXPECTED_EVENT_NOT_RECEIVED", {"events": events}
                )
            return RunnerActionOutcome(
                action.identifier,
                action.action_type,
                ResultStatus.PASSED,
                started_at,
                datetime.now(UTC),
                expected={"event": expected_event},
                actual={"events": events},
            )
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            return self._failed(action, started_at, "SSE_TRANSPORT_ERROR", error=str(exc))

    @staticmethod
    async def _read_events(
        response: httpx.Response,
        max_events: int,
        cancellation: asyncio.Event,
    ) -> tuple[list[dict[str, str]], bool]:
        """Read bounded SSE events and stop promptly when cancellation is requested."""
        events: list[dict[str, str]] = []
        current: dict[str, str] = {}
        async for line in response.aiter_lines():
            if cancellation.is_set():
                return events, True
            if not line:
                current, complete = SseExecutor._complete_event(events, current, max_events)
                if complete:
                    break
            else:
                SseExecutor._append_field(current, line)
        SseExecutor._complete_event(events, current, max_events)
        return events, False

    @staticmethod
    def _complete_event(
        events: list[dict[str, str]], current: dict[str, str], max_events: int
    ) -> tuple[dict[str, str], bool]:
        """Append a completed event and report whether the configured bound was reached."""
        if not current or len(events) >= max_events:
            return current, len(events) >= max_events
        events.append(current)
        return {}, len(events) >= max_events

    @staticmethod
    def _append_field(current: dict[str, str], line: str) -> None:
        """Add one SSE field while ignoring comments and malformed lines."""
        if line.startswith(":") or ":" not in line:
            return
        field, value = line.split(":", 1)
        value = value.lstrip()
        current[field] = (
            f"{current[field]}\n{value}" if field == "data" and field in current else value
        )

    @staticmethod
    def _failed(
        action: CompiledAction,
        started_at: datetime,
        code: str,
        actual: Mapping[str, object] | None = None,
        error: str | None = None,
    ) -> RunnerActionOutcome:
        """Build a failed action outcome with normalized error information."""
        return RunnerActionOutcome(
            action.identifier,
            action.action_type,
            ResultStatus.FAILED,
            started_at,
            datetime.now(UTC),
            actual=actual,
            error_code=code,
            error_message=error or code.replace("_", " ").lower(),
        )
