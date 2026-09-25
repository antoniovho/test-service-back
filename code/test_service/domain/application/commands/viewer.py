"""Commands for Viewer integration use cases."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublishViewerProjectionCommand:
    """Request to asynchronously publish a canonical projection."""


@dataclass(frozen=True, slots=True)
class CheckViewerDriftCommand:
    """Request to asynchronously check one Viewer projection for drift."""
