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
                summary=f"{snapshot.test_key} v{snapshot.version} - {snapshot.name}",
                description=cls._test_case_description(snapshot),
                labels=cls._labels(snapshot.metadata),
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
                precondition_external_ids=cls._external_ids(
                    (reference.identifier for reference in snapshot.preconditions), external_ids
                ),
            )
        if isinstance(snapshot, Precondition):
            return ViewerProjection(
                record=record,
                summary=f"{snapshot.precondition_key} v{snapshot.version} - {snapshot.name}",
                description=cls._precondition_description(snapshot),
                definition=cls._definition_text(snapshot.validation_definition),
                labels=cls._labels(snapshot.metadata),
            )
        if isinstance(snapshot, TestSet):
            return ViewerProjection(
                record=record,
                summary=snapshot.name,
                description=snapshot.description,
                test_external_ids=cls._external_ids(snapshot.items, external_ids),
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
            test_external_ids=cls._external_ids(included_ids, external_ids),
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
    def _definition_text(definition: Definition) -> str:
        content = json.dumps(
            [
                {
                    "id": action.identifier,
                    "type": action.action_type,
                    "configuration": dict(action.configuration),
                }
                for action in definition.actions
            ],
            sort_keys=True,
            indent=2,
        )
        return f"{{code:json}}\n{content}\n{{code}}"

    @staticmethod
    def _test_case_description(test_case: TestCase) -> str:
        metadata = dict(test_case.metadata or {})
        sections = [
            f"*Summary*\n{test_case.summary}",
            f"*Objective*\n{test_case.objective}",
            "\n".join(
                (
                    "*Classification*",
                    f"- *Type*: {test_case.test_type.value}",
                    f"- *Level*: {test_case.test_level.value}",
                    f"- *Priority*: {test_case.priority.value}",
                    f"- *Timeout*: {test_case.timeout_seconds} seconds",
                )
            ),
            ViewerProjectionBuilder._source_section(
                "Test key", test_case.test_key, test_case.version, metadata.get("source")
            ),
        ]
        metadata_items = (
            (key, value)
            for key, value in metadata.items()
            if key not in {"labels", "objective", "source"}
        )
        sections.extend(ViewerProjectionBuilder._metadata_section(metadata_items))
        return "\n\n".join(sections)

    @staticmethod
    def _precondition_description(precondition: Precondition) -> str:
        return "\n\n".join(
            (
                precondition.description,
                ViewerProjectionBuilder._source_section(
                    "Precondition key",
                    precondition.precondition_key,
                    precondition.version,
                    (precondition.metadata or {}).get("source"),
                ),
            )
        )

    @staticmethod
    def _source_section(key_label: str, key: str, version: int, source: object) -> str:
        lines = ["*Source*", f"- *{key_label}*: {key}", f"- *Version*: {version}"]
        if isinstance(source, str) and source:
            lines.append(f"- *Documentation*: {source}")
        return "\n".join(lines)

    @staticmethod
    def _metadata_section(items: Iterable[tuple[str, object]]) -> tuple[str, ...]:
        lines = [f"- {key.replace('_', ' ').title()}: {value}" for key, value in items]
        return ("*Metadata*\n" + "\n".join(lines),) if lines else ()

    @staticmethod
    def _labels(metadata: Mapping[str, object] | None) -> tuple[str, ...]:
        labels = metadata.get("labels") if metadata else ()
        if not isinstance(labels, Iterable) or isinstance(labels, (str, bytes)):
            return ()
        return tuple(dict.fromkeys(label for label in labels if isinstance(label, str) and label))
