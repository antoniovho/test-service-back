import asyncio

import httpx

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
