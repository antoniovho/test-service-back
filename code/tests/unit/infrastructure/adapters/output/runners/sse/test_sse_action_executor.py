import asyncio
import json

import httpx
import pytest

from test_service.domain.model.execution.execution import ResultStatus
from test_service.domain.ports.output.runners.runner_dtos import CompiledAction
from test_service.infrastructure.adapters.output.runners.sse.sse_action_executor import (
    SseExecutor,
)


async def test_when_receiving_expected_event_expect_normalized_passed_outcome() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            content=b"event: order-created\ndata: first\ndata: second\n\n",
            headers={"content-type": "text/event-stream"},
        )

    action = CompiledAction(
        identifier="await-order",
        action_type="SSE",
        position=0,
        configuration={
            "url": "{{baseUrl}}/events",
            "headers": {"X-Tenant": "{{tenant}}"},
            "maxEvents": 1,
            "expectedEvent": "order-created",
        },
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        outcome = await SseExecutor().execute(
            client,
            action,
            {"baseUrl": "https://api.example.test", "tenant": "acme"},
            asyncio.Event(),
        )

    assert requests[0].url == "https://api.example.test/events"
    assert requests[0].headers["X-Tenant"] == "acme"
    assert outcome.status is ResultStatus.PASSED
    assert outcome.expected == {"event": "order-created"}
    assert outcome.actual["events"] == [{"event": "order-created", "data": "first\nsecond"}]
    assert outcome.actual["responseTimeMs"] >= 0


async def test_when_expected_event_is_not_received_expect_failed_outcome() -> None:
    action = CompiledAction(
        "await-order",
        "SSE",
        0,
        {"url": "https://api.example.test/events", "expectedEvent": "order-created"},
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"event: other\ndata: value\n\n")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_EXPECTED_EVENT_NOT_RECEIVED"


async def test_when_posting_and_expected_data_is_received_expect_passed_outcome() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=b"event: completed\ndata: [DONE]\n\n")

    action = CompiledAction(
        "await-completion",
        "SSE",
        0,
        {
            "url": "https://api.example.test/events",
            "method": "POST",
            "json": {"jobId": "42"},
            "expectedData": "[DONE]",
            "expectedDone": True,
        },
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert requests[0].method == "POST"
    assert json.loads(requests[0].content) == {"jobId": "42"}
    assert outcome.status is ResultStatus.PASSED
    assert outcome.expected == {"data": "[DONE]", "done": True}


async def test_when_sse_content_type_and_json_chunk_match_expect_passed_outcome() -> None:
    chunk_schema = {
        "type": "object",
        "required": ["object"],
        "properties": {"object": {"const": "chat.completion.chunk"}},
    }
    action = CompiledAction(
        "stream-chat",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "expectedContentType": "text/event-stream",
            "expectedDataJsonSchema": chunk_schema,
            "expectedDone": True,
            "maxEvents": 2,
            "maxResponseTimeMs": 30000,
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=(b'data: {"object":"chat.completion.chunk"}\n\ndata: [DONE]\n\n'),
            headers={"content-type": "text/event-stream; charset=utf-8"},
        )
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.PASSED
    assert outcome.expected["contentType"] == "text/event-stream"
    assert outcome.expected["dataJsonSchema"] == chunk_schema


async def test_when_sse_chunk_is_not_json_expect_failed_outcome() -> None:
    action = CompiledAction(
        "stream-chat",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "expectedDataJsonSchema": {"type": "object"},
            "expectedDone": True,
            "maxEvents": 2,
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"data: not-json\n\ndata: [DONE]\n\n")
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_INVALID_JSON_DATA"


async def test_when_sse_content_type_is_unexpected_expect_failed_outcome() -> None:
    action = CompiledAction(
        "stream-chat",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "expectedContentType": "text/event-stream",
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=b"data: payload\n\n",
            headers={"content-type": "text/plain"},
        )
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_CONTENT_TYPE_MISMATCH"


async def test_when_sse_delta_fragments_match_expect_passed_outcome() -> None:
    chunk_schema = {
        "type": "object",
        "required": ["choices"],
        "properties": {
            "choices": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "object", "required": ["delta"]},
            }
        },
    }
    action = CompiledAction(
        "stream-chat",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "expectedDataJsonSchema": chunk_schema,
            "expectedConcatenatedContent": "STREAMING_TEST_RESPONSE",
            "expectedDone": True,
            "maxEvents": 3,
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=(
                b'data: {"choices":[{"delta":{"content":"STREAMING_"}}]}\n\n'
                b'data: {"choices":[{"delta":{"content":"TEST_RESPONSE"}}]}\n\n'
                b"data: [DONE]\n\n"
            ),
        )
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.PASSED
    assert outcome.expected["concatenatedContent"] == "STREAMING_TEST_RESPONSE"


async def test_when_sse_delta_fragments_differ_expect_failed_outcome() -> None:
    action = CompiledAction(
        "stream-chat",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "expectedConcatenatedContent": "expected",
            "expectedDone": True,
            "maxEvents": 2,
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=b'data: {"choices":[{"delta":{"content":"actual"}}]}\n\ndata: [DONE]\n\n',
        )
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_RECONSTRUCTED_CONTENT_MISMATCH"


async def test_when_sse_data_follows_done_marker_expect_failed_outcome() -> None:
    action = CompiledAction(
        "stream-chat",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "expectedDone": True,
            "maxEvents": 2,
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"data: [DONE]\n\ndata: unexpected\n\n")
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_DONE_NOT_RECEIVED"


async def test_when_final_sse_chunk_has_consistent_usage_expect_passed_outcome() -> None:
    chunk_schema = {
        "type": "object",
        "required": ["object"],
        "properties": {"object": {"const": "chat.completion.chunk"}},
    }
    final_schema = {
        "type": "object",
        "required": ["usage"],
        "properties": {
            "usage": {
                "type": "object",
                "required": ["prompt_tokens", "completion_tokens", "total_tokens"],
                "properties": {
                    "prompt_tokens": {"type": "integer", "minimum": 0},
                    "completion_tokens": {"type": "integer", "minimum": 0},
                    "total_tokens": {"type": "integer", "minimum": 0},
                },
            }
        },
    }
    action = CompiledAction(
        "stream-usage",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "expectedDataJsonSchema": chunk_schema,
            "expectedFinalDataJsonSchema": final_schema,
            "validateUsageTotals": True,
            "expectedDone": True,
            "maxEvents": 3,
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=(
                b'data: {"object":"chat.completion.chunk","choices":[]}\n\n'
                b'data: {"object":"chat.completion.chunk","usage":{"prompt_tokens":9,'
                b'"completion_tokens":1,"total_tokens":10}}\n\n'
                b"data: [DONE]\n\n"
            ),
        )
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.PASSED
    assert outcome.expected["usageTotalsConsistent"] is True


async def test_when_final_sse_usage_totals_are_inconsistent_expect_failed_outcome() -> None:
    action = CompiledAction(
        "stream-usage",
        "SSE",
        0,
        {
            "url": "https://api.example.test/chat/completions",
            "validateUsageTotals": True,
            "expectedDone": True,
            "maxEvents": 2,
        },
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=(
                b'data: {"usage":{"prompt_tokens":9,"completion_tokens":1,"total_tokens":11}}\n\n'
                b"data: [DONE]\n\n"
            ),
        )
    )

    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_USAGE_TOTALS_MISMATCH"


async def test_when_response_exceeds_maximum_time_expect_failed_outcome(monkeypatch) -> None:
    ticks = iter((0.0, 0.1))
    monkeypatch.setattr(
        "test_service.infrastructure.adapters.output.runners.sse.sse_action_executor.perf_counter",
        lambda: next(ticks),
    )
    action = CompiledAction(
        "await-order",
        "SSE",
        0,
        {"url": "https://api.example.test/events", "maxResponseTimeMs": 50},
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"event: order-created\n\n")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_RESPONSE_TIME_EXCEEDED"


async def test_when_stream_is_cancelled_expect_skipped_outcome() -> None:
    action = CompiledAction("await-order", "SSE", 0, {"url": "https://api.example.test/events"})
    cancellation = asyncio.Event()
    cancellation.set()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"event: order-created\n\n")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        outcome = await SseExecutor().execute(client, action, {}, cancellation)

    assert outcome.status is ResultStatus.SKIPPED
    assert outcome.error_code == "CANCELLED"


@pytest.mark.parametrize(
    "configuration",
    [[], {"url": ""}],
    ids=["not-an-object", "empty-url"],
)
async def test_when_sse_configuration_is_invalid_expect_transport_error(configuration) -> None:
    action = CompiledAction("await-order", "SSE", 0, configuration)
    async with httpx.AsyncClient() as client:
        outcome = await SseExecutor().execute(client, action, {}, asyncio.Event())

    assert outcome.status is ResultStatus.FAILED
    assert outcome.error_code == "SSE_TRANSPORT_ERROR"
