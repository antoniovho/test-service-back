"""Build canonical Viewer projections from local immutable snapshots."""

import json
from collections.abc import Iterable, Mapping
from uuid import UUID

from test_service.domain.model.authoring.definition import Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.viewer_projection_integrity_exception import (
    ViewerProjectionIntegrityException,
)
from test_service.domain.model.viewer.projection import ViewerProjection, ViewerProjectionStep
from test_service.domain.model.viewer.records import ViewerSyncRecord

type ViewerSnapshot = TestCase | Precondition | TestSet | TestPlan


class ViewerProjectionBuilder:
    """Translate local snapshots and resolved external dependencies into Viewer data."""

    @classmethod
    def build(
        cls,
        record: ViewerSyncRecord,
        snapshot: ViewerSnapshot,
        snapshots_by_id: Mapping[UUID, ViewerSnapshot],
        external_ids: Mapping[UUID, str],
    ) -> ViewerProjection:
        """Return a Viewer projection for one snapshot with resolved dependencies."""
        if isinstance(snapshot, TestCase):
            return ViewerProjection(
                record=record,
                summary=snapshot.name,
                description=snapshot.summary,
                steps=tuple(
                    ViewerProjectionStep(
                        action=f"{action.identifier}: {action.action_type}",
                        data=json.dumps(
                            dict(action.configuration), sort_keys=True, separators=(",", ":")
                        ),
                        result=snapshot.objective,
                    )
                    for action in snapshot.definition.actions
                ),
                precondition_issue_ids=cls._external_ids(
                    (reference.identifier for reference in snapshot.preconditions), external_ids
                ),
            )
        if isinstance(snapshot, Precondition):
            return ViewerProjection(
                record=record,
                summary=snapshot.name,
                description=cls._definition_text(
                    snapshot.description, snapshot.validation_definition
                ),
            )
        if isinstance(snapshot, TestSet):
            return ViewerProjection(
                record=record,
                summary=snapshot.name,
                description=snapshot.description,
                test_issue_ids=cls._external_ids(snapshot.items, external_ids),
            )
        # Test Plan
        test_case_ids = list(snapshot.test_case_ids)
        for test_set_id in snapshot.test_set_ids:
            test_set = snapshots_by_id.get(test_set_id)
            if not isinstance(test_set, TestSet):
                raise ViewerProjectionIntegrityException(
                    f"test plan references unavailable active test set '{test_set_id}'"
                )
            test_case_ids.extend(test_set.items)
        included_ids = tuple(
            identifier
            for identifier in dict.fromkeys(test_case_ids)
            if identifier not in snapshot.exclusions
        )
        return ViewerProjection(
            record=record,
            summary=snapshot.name,
            description=snapshot.description,
            test_issue_ids=cls._external_ids(included_ids, external_ids),
        )

    @staticmethod
    def _external_ids(
        identifiers: Iterable[UUID], external_ids: Mapping[UUID, str]
    ) -> tuple[str, ...]:
        resolved_ids = []
        for identifier in identifiers:
            try:
                resolved_ids.append(external_ids[identifier])
            except KeyError as error:
                raise ViewerProjectionIntegrityException(
                    f"Viewer projection dependency '{identifier}' is not synchronized"
                ) from error
        return tuple(resolved_ids)

    @staticmethod
    def _definition_text(description: str, definition: Definition) -> str:
        actions = "\n".join(
            f"{action.identifier}: {action.action_type}\n"
            f"{json.dumps(dict(action.configuration), sort_keys=True, separators=(',', ':'))}"
            for action in definition.actions
        )
        return f"{description}\n\n{actions}"
