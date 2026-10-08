import asyncio

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
    assert outcome.actual == {"events": [{"event": "order-created", "data": "first\nsecond"}]}


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
