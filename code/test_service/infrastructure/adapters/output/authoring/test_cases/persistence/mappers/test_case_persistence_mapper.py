"""Mapping between Test Case domain objects and SQLAlchemy DTOs."""

from typing import TypedDict, cast
from uuid import uuid4

from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import (
    PreconditionReference,
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.dtos.test_case_dto import (  # noqa: E501
    TestCaseDTO,
    TestCasePreconditionDTO,
)


class ActionJson(TypedDict):
    """Persistence representation of an Action."""

    identifier: str
    action_type: str
    configuration: dict[str, object]
    source: str | None


class DefinitionJson(TypedDict):
    """Persistence representation of a Definition."""

    schema_version: str
    variables: dict[str, str]
    actions: list[ActionJson]


class TestCasePersistenceMapper:
    """Translate Test Case data at the domain and persistence boundary."""

    @staticmethod
    def to_dto(test_case: TestCase) -> TestCaseDTO:
        """Create a persistence DTO from one Test Case aggregate."""
        return TestCaseDTO(
            id=test_case.identifier,
            project_key=test_case.project_key,
            test_key=test_case.test_key,
            version=test_case.version,
            name=test_case.name,
            summary=test_case.summary,
            objective=test_case.objective,
            test_type=test_case.test_type.value,
            test_level=test_case.test_level.value,
            priority=test_case.priority.value,
            status=test_case.status.value,
            definition=TestCasePersistenceMapper._definition_to_json(test_case.definition),
            timeout_seconds=test_case.timeout_seconds,
            metadata_=dict(test_case.metadata or {}),
            created_at=test_case.created_at,
            created_by=test_case.created_by,
            precondition_links=[
                TestCasePreconditionDTO(
                    id=uuid4(),
                    precondition_id=reference.identifier,
                    position=position,
                )
                for position, reference in enumerate(test_case.preconditions)
            ],
        )

    @staticmethod
    def to_domain(test_case: TestCaseDTO) -> TestCase:
        """Create a Test Case aggregate from a fully loaded DTO."""
        return TestCase(
            identifier=test_case.id,
            project_key=test_case.project_key,
            test_key=test_case.test_key,
            version=test_case.version,
            name=test_case.name,
            summary=test_case.summary,
            objective=test_case.objective,
            test_type=TestType(test_case.test_type),
            test_level=TestLevel(test_case.test_level),
            priority=Priority(test_case.priority),
            status=VersionStatus(test_case.status),
            definition=TestCasePersistenceMapper._definition_to_domain(
                cast(DefinitionJson, test_case.definition)
            ),
            timeout_seconds=test_case.timeout_seconds,
            metadata=test_case.metadata_,
            created_at=test_case.created_at,
            created_by=test_case.created_by,
            preconditions=tuple(
                PreconditionReference(
                    identifier=link.precondition_id,
                    precondition_key=link.precondition.precondition_key,
                    version=link.precondition.version,
                )
                for link in test_case.precondition_links
            ),
        )

    @staticmethod
    def _definition_to_json(definition: Definition) -> DefinitionJson:
        """Serialize a Definition into its persistence representation."""
        return {
            "schema_version": definition.schema_version,
            "variables": dict(definition.variables),
            "actions": [
                {
                    "identifier": action.identifier,
                    "action_type": action.action_type,
                    "configuration": dict(action.configuration),
                    "source": action.source,
                }
                for action in definition.actions
            ],
        }

    @staticmethod
    def _definition_to_domain(value: DefinitionJson) -> Definition:
        """Deserialize a persisted Definition into the domain model."""
        return Definition(
            schema_version=value["schema_version"],
            variables=value["variables"],
            actions=tuple(
                Action(
                    identifier=action["identifier"],
                    action_type=action["action_type"],
                    configuration=action["configuration"],
                    source=action["source"],
                )
                for action in value["actions"]
            ),
        )
