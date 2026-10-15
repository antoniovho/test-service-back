"""SSE action execution for runner adapters."""

import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from time import perf_counter

import httpx
from jsonschema import Draft202012Validator, SchemaError, ValidationError

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledAction,
    RunnerActionOutcome,
)
from test_service.infrastructure.adapters.output.runners.tavern.variable_renderer import (
    render_service_variables,
)

_DONE_MARKER = "[DONE]"


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
            config = render_service_variables(action.configuration, context, False)
            if not isinstance(config, dict):
                raise ValueError("SSE action configuration must be an object")
            url = config.get("url")
            if not isinstance(url, str) or not url:
                raise ValueError("SSE action configuration must define a non-empty url")
            timeout = float(config.get("receiveTimeoutSeconds", 30))
            max_events = int(config.get("maxEvents", 1))
            method = config.get("method", "GET")
            if method not in {"GET", "POST"}:
                raise ValueError("SSE action method must be GET or POST")
            expected_data_schema = config.get("expectedDataJsonSchema")
            expected_final_data_schema = config.get("expectedFinalDataJsonSchema")
            try:
                data_validator = self._build_validator(expected_data_schema)
                final_data_validator = self._build_validator(expected_final_data_schema)
            except (SchemaError, TypeError):
                return self._failed(action, started_at, "SSE_INVALID_EXPECTED_SCHEMA")
            expected_content_type = config.get("expectedContentType")
            params = config.get("query", config.get("params"))
            request_started_at = perf_counter()
            async with client.stream(
                method,
                url,
                headers=config.get("headers"),
                params=params,
                json=config.get("json"),
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                if not self._content_type_matches(response, expected_content_type):
                    return self._failed(action, started_at, "SSE_CONTENT_TYPE_MISMATCH")
                events, cancelled = await self._read_events(response, max_events, cancellation)
            response_time_ms = round((perf_counter() - request_started_at) * 1000)
            if cancelled:
                return RunnerActionOutcome(
                    action.identifier,
                    action.action_type,
                    ResultStatus.SKIPPED,
                    started_at,
                    datetime.now(UTC),
                    actual={"events": events, "responseTimeMs": response_time_ms},
                    error_code="CANCELLED",
                    error_message="SSE stream cancelled",
                )
            error_code, actual = self._validate_events(
                events,
                config,
                data_validator,
                final_data_validator,
            )
            if error_code is not None:
                return self._failed(action, started_at, error_code, actual)
            max_response_time_ms = config.get("maxResponseTimeMs")
            if max_response_time_ms is not None and response_time_ms > max_response_time_ms:
                return self._failed(
                    action,
                    started_at,
                    "SSE_RESPONSE_TIME_EXCEEDED",
                    {"events": events, "responseTimeMs": response_time_ms},
                )
            return RunnerActionOutcome(
                action.identifier,
                action.action_type,
                ResultStatus.PASSED,
                started_at,
                datetime.now(UTC),
                expected=self._expected_values(config),
                actual={"events": events, "responseTimeMs": response_time_ms},
            )
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            return self._failed(action, started_at, "SSE_TRANSPORT_ERROR", error=str(exc))

    @staticmethod
    def _build_validator(schema: object) -> Draft202012Validator | None:
        if schema is None:
            return None
        if not isinstance(schema, Mapping):
            raise TypeError("SSE response schema must be an object")
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema)

    @staticmethod
    def _content_type_matches(response: httpx.Response, expected: object) -> bool:
        if expected is None:
            return True
        actual = response.headers.get("content-type", "").split(";", 1)[0]
        return isinstance(expected, str) and actual.strip().lower() == expected.lower()

    @classmethod
    def _validate_events(
        cls,
        events: list[dict[str, str]],
        config: Mapping[str, object],
        data_validator: Draft202012Validator | None,
        final_data_validator: Draft202012Validator | None,
    ) -> tuple[str | None, Mapping[str, object] | None]:
        error_code, needs_event_details = cls._validate_event_requirements(events, config)
        if error_code is not None:
            actual = {"events": events} if needs_event_details else None
            return error_code, actual
        return cls._validate_json_data(events, config, data_validator, final_data_validator), None

    @staticmethod
    def _validate_event_requirements(
        events: list[dict[str, str]], config: Mapping[str, object]
    ) -> tuple[str | None, bool]:
        expected_event = config.get("expectedEvent")
        if expected_event and not any(item.get("event") == expected_event for item in events):
            return "SSE_EXPECTED_EVENT_NOT_RECEIVED", True
        expected_data = config.get("expectedData")
        if expected_data is not None and not any(
            item.get("data") == expected_data for item in events
        ):
            return "SSE_EXPECTED_DATA_NOT_RECEIVED", True
        expected_done = config.get("expectedDone")
        data_events = [item["data"] for item in events if "data" in item]
        done_received = _DONE_MARKER in data_events
        if expected_done is True and (not data_events or data_events[-1] != _DONE_MARKER):
            return "SSE_DONE_NOT_RECEIVED", True
        if expected_done is False and done_received:
            return "SSE_UNEXPECTED_DONE", True
        return None, False

    @classmethod
    def _validate_json_data(
        cls,
        events: list[dict[str, str]],
        config: Mapping[str, object],
        data_validator: Draft202012Validator | None,
        final_data_validator: Draft202012Validator | None,
    ) -> str | None:
        expected_content = config.get("expectedConcatenatedContent")
        validate_usage_totals = config.get("validateUsageTotals", False)
        needs_json = any(
            (
                data_validator is not None,
                final_data_validator is not None,
                expected_content is not None,
                validate_usage_totals is True,
            )
        )
        if not needs_json:
            return None
        chunks, error_code = cls._decode_json_chunks(events, data_validator)
        if error_code is not None:
            return error_code
        if (data_validator is not None or final_data_validator is not None) and not chunks:
            return "SSE_NO_JSON_DATA"
        if final_data_validator is not None and not cls._matches_schema(
            final_data_validator, chunks[-1]
        ):
            return "SSE_FINAL_DATA_SCHEMA_MISMATCH"
        if validate_usage_totals is True and not cls._usage_totals_are_consistent(chunks):
            return "SSE_USAGE_TOTALS_MISMATCH"
        if expected_content is not None and not cls._content_matches(chunks, expected_content):
            return "SSE_RECONSTRUCTED_CONTENT_MISMATCH"
        return None

    @staticmethod
    def _decode_json_chunks(
        events: list[dict[str, str]], data_validator: Draft202012Validator | None
    ) -> tuple[list[object], str | None]:
        chunks: list[object] = []
        for item in events:
            event_data = item.get("data")
            if event_data is None or event_data == _DONE_MARKER:
                continue
            try:
                chunk = json.loads(event_data)
            except json.JSONDecodeError:
                return [], "SSE_INVALID_JSON_DATA"
            if data_validator is not None and not SseExecutor._matches_schema(
                data_validator, chunk
            ):
                return [], "SSE_DATA_SCHEMA_MISMATCH"
            chunks.append(chunk)
        return chunks, None

    @staticmethod
    def _matches_schema(validator: Draft202012Validator, value: object) -> bool:
        try:
            validator.validate(value)
        except ValidationError:
            return False
        return True

    @staticmethod
    def _usage_totals_are_consistent(chunks: list[object]) -> bool:
        if not chunks or not isinstance(chunks[-1], Mapping):
            return False
        usage = chunks[-1].get("usage")
        if not isinstance(usage, Mapping):
            return False
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if (
            not isinstance(prompt_tokens, int)
            or isinstance(prompt_tokens, bool)
            or not isinstance(completion_tokens, int)
            or isinstance(completion_tokens, bool)
            or not isinstance(total_tokens, int)
            or isinstance(total_tokens, bool)
        ):
            return False
        return (
            prompt_tokens >= 0
            and completion_tokens >= 0
            and total_tokens >= 0
            and total_tokens == prompt_tokens + completion_tokens
        )

    @staticmethod
    def _content_matches(chunks: list[object], expected_content: object) -> bool:
        if not isinstance(expected_content, str):
            return False
        fragments: list[str] = []
        for chunk in chunks:
            choices = chunk.get("choices", []) if isinstance(chunk, Mapping) else []
            if choices and isinstance(choices[0], Mapping):
                delta = choices[0].get("delta", {})
                if isinstance(delta, Mapping):
                    content = delta.get("content")
                    if isinstance(content, str):
                        fragments.append(content)
        return "".join(fragments) == expected_content

    @staticmethod
    def _expected_values(config: Mapping[str, object]) -> Mapping[str, object]:
        expected_keys = {
            "expectedEvent": "event",
            "expectedData": "data",
            "expectedDataJsonSchema": "dataJsonSchema",
            "expectedFinalDataJsonSchema": "finalDataJsonSchema",
            "expectedConcatenatedContent": "concatenatedContent",
            "expectedContentType": "contentType",
            "maxResponseTimeMs": "maxResponseTimeMs",
        }
        expected = {
            output_key: config[input_key]
            for input_key, output_key in expected_keys.items()
            if input_key in config
        }
        if config.get("validateUsageTotals") is True:
            expected["usageTotalsConsistent"] = True
        if "expectedDone" in config:
            expected["done"] = config["expectedDone"]
        return expected

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
