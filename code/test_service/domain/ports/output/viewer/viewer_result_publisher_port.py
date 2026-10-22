"""External viewer contract for execution-result publication."""

from typing import Protocol

from test_service.domain.model.viewer.execution_result_projection import (
    ViewerExecutionResultIdentity,
    ViewerExecutionResultProjection,
)


class ViewerResultPublisherPort(Protocol):
    """Publish one fully resolved execution-result projection."""

    async def publish_execution_result(
        self, projection: ViewerExecutionResultProjection
    ) -> ViewerExecutionResultIdentity:
        """Create or update the external Test Execution and its Test Runs."""
        ...
