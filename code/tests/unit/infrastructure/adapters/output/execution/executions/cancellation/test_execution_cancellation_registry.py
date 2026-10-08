from uuid import uuid4

from test_service.infrastructure.adapters.output.execution.executions.cancellation.execution_cancellation_registry import (  # noqa: E501
    ExecutionCancellationRegistry,
)


class TestExecutionCancellationRegistry:
    def test_when_cancellation_is_requested_for_registered_execution_expect_event_set(self) -> None:
        registry = ExecutionCancellationRegistry()
        execution_id = uuid4()
        cancellation = registry.register(execution_id)

        registry.request_cancellation(execution_id)

        assert cancellation.is_set()

    def test_when_execution_is_unregistered_expect_future_cancellation_ignored(self) -> None:
        registry = ExecutionCancellationRegistry()
        execution_id = uuid4()
        cancellation = registry.register(execution_id)
        registry.unregister(execution_id)

        registry.request_cancellation(execution_id)

        assert not cancellation.is_set()
