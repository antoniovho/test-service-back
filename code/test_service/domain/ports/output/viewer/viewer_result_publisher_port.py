"""External viewer contract for execution-result publication."""

from typing import Protocol

from test_service.domain.model.viewer.execution_result_projection import (
    ViewerExecutionResultIdentity,
    ViewerExecutionResultProjection,
)
from test_service.domain.model.viewer.records import ViewerType


class ViewerResultPublisherPort(Protocol):
    """Publish one fully resolved execution-result projection."""

    @property
    def viewer_type(self) -> ViewerType:
        """Return the external viewer platform implemented by this publisher."""
        ...

    async def publish_execution_result(
        self, projection: ViewerExecutionResultProjection
    ) -> ViewerExecutionResultIdentity:
        """Create or update the external Test Execution and its Test Runs."""
        ...
