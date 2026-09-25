"""Commands for Viewer integration use cases."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublishViewerProjectionCommand:
    """Request to asynchronously publish the ACTIVE version of every entity in a project.

    Args:
        project_key: Owning project key.
    """

    project_key: str


@dataclass(frozen=True, slots=True)
class CheckViewerDriftCommand:
    """Request to asynchronously check every published entity in a project for drift.

    Args:
        project_key: Owning project key.
    """

    project_key: str
