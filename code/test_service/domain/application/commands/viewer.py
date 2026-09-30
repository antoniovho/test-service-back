"""Commands for Viewer integration use cases."""

from dataclasses import dataclass

from test_service.domain.model.viewer.records import ViewerType


@dataclass(frozen=True, slots=True)
class PublishViewerProjectionCommand:
    """Request to asynchronously publish the ACTIVE version of every entity in a project.

    Args:
        project_key: Owning project key.
        viewer_type: External Viewer targeted by the publication.
    """

    project_key: str
    viewer_type: ViewerType


@dataclass(frozen=True, slots=True)
class CheckViewerDriftCommand:
    """Request to asynchronously check every published entity in a project for drift.

    Args:
        project_key: Owning project key.
        viewer_type: External Viewer targeted by the drift check.
    """

    project_key: str
    viewer_type: ViewerType
