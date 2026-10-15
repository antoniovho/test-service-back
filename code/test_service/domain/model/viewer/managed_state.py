"""Normalized content managed by an external Viewer provider."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from test_service.domain.model.viewer.projection import ViewerProjection, ViewerProjectionStep
from test_service.domain.model.viewer.records import ViewerEntityType


@dataclass(frozen=True, slots=True)
class ViewerManagedState:
    """Provider-managed projection content, excluding Jira presentation fields."""

    entity_type: ViewerEntityType
    definition: str | None = None
    steps: tuple[ViewerProjectionStep, ...] = ()
    related_external_ids: tuple[str, ...] = ()

    @classmethod
    def from_projection(cls, projection: ViewerProjection) -> ViewerManagedState:
        """Build the normalized content expected for a canonical projection."""
        entity_type = projection.record.entity_type
        if entity_type is ViewerEntityType.TEST_CASE:
            return cls(
                entity_type=entity_type,
                steps=tuple(cls._normalized_step(step) for step in projection.steps),
                related_external_ids=cls._normalized_external_ids(
                    projection.precondition_external_ids
                ),
            )
        if entity_type is ViewerEntityType.PRECONDITION:
            return cls(
                entity_type=entity_type, definition=cls._normalized_text(projection.description)
            )
        return cls(
            entity_type=entity_type,
            related_external_ids=cls._normalized_external_ids(projection.test_external_ids),
        )

    @classmethod
    def from_remote(
        cls,
        entity_type: ViewerEntityType,
        *,
        definition: str | None = None,
        steps: tuple[ViewerProjectionStep, ...] = (),
        related_external_ids: tuple[str, ...] = (),
    ) -> ViewerManagedState:
        """Build normalized managed state from provider-returned fields."""
        return cls(
            entity_type=entity_type,
            definition=cls._normalized_text(definition),
            steps=tuple(cls._normalized_step(step) for step in steps),
            related_external_ids=cls._normalized_external_ids(related_external_ids),
        )

    @property
    def projection_hash(self) -> str:
        """Return a stable SHA-256 digest of the managed content."""
        encoded_state = json.dumps(
            self._canonical_value(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
        return sha256(encoded_state).hexdigest()

    def differing_fields(self, actual: ViewerManagedState) -> tuple[str, ...]:
        """Return safe names of managed fields that differ from the remote state."""
        differences: list[str] = []
        if self.entity_type != actual.entity_type:
            differences.append("entity_type")
        if self.definition != actual.definition:
            differences.append("definition")
        if self.steps != actual.steps:
            differences.append("steps")
        if self.related_external_ids != actual.related_external_ids:
            differences.append(self._relationship_field)
        return tuple(differences)

    @property
    def _relationship_field(self) -> str:
        if self.entity_type is ViewerEntityType.TEST_CASE:
            return "preconditions"
        return "tests"

    def _canonical_value(self) -> dict[str, object]:
        return {
            "entity_type": self.entity_type.value,
            "definition": self.definition,
            "steps": [
                {"action": step.action, "data": step.data, "result": step.result}
                for step in self.steps
            ],
            "related_external_ids": list(self.related_external_ids),
        }

    @classmethod
    def _normalized_step(cls, step: ViewerProjectionStep) -> ViewerProjectionStep:
        return ViewerProjectionStep(
            action=cls._normalized_text(step.action) or "",
            data=cls._normalized_text(step.data),
            result=cls._normalized_text(step.result),
        )

    @staticmethod
    def _normalized_external_ids(external_ids: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(set(external_ids)))

    @staticmethod
    def _normalized_text(value: str | None) -> str | None:
        if value is None:
            return None
        return "\n".join(line.strip() for line in value.replace("\r\n", "\n").split("\n")).strip()
