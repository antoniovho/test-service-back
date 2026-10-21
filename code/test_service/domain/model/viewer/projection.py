"""Canonical data passed from Viewer publication to an external provider."""

from dataclasses import dataclass

from test_service.domain.model.viewer.records import ViewerSyncRecord


@dataclass(frozen=True, slots=True)
class ViewerProjectionStep:
    """One manual verification step in an external Viewer projection."""

    action: str
    data: str | None
    result: str | None


@dataclass(frozen=True, slots=True)
class ViewerProjection:
    """Canonical projection of one local snapshot and its resolved dependencies."""

    record: ViewerSyncRecord
    summary: str
    description: str | None = None
    definition: str | None = None
    labels: tuple[str, ...] = ()
    steps: tuple[ViewerProjectionStep, ...] = ()
    precondition_external_ids: tuple[str, ...] = ()
    test_external_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ViewerExternalIdentity:
    """Stable provider identity returned after a successful publication."""

    external_id: str
    external_key: str
