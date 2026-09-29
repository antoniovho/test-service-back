"""Use case implementation: create Test Case version."""

from uuid import uuid4

from test_service.domain.application.commands.authoring import CreateTestCaseVersionCommand
from test_service.domain.application.services.precondition_references import (
    PreconditionReferenceResolver,
)
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class CreateTestCaseVersionUseCaseImpl(CreateTestCaseVersionUseCase):
    """Creates a new draft snapshot from an existing Test Case snapshot."""

    def __init__(
        self,
        test_case_repository: TestCasePersistencePort,
        precondition_reference_resolver: PreconditionReferenceResolver,
    ) -> None:
        self._test_case_repository = test_case_repository
        self._precondition_reference_resolver = precondition_reference_resolver

    async def execute(self, request: CreateTestCaseVersionCommand) -> TestCase:
        """Create and persist the next immutable Test Case version."""
        source = await self._test_case_repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test case",
                str(request.source_id),
                f"project '{request.project_key}'",
            )

        latest_version = await self._test_case_repository.find_latest_version(
            source.project_key, source.test_key
        )
        next_version = (latest_version or source.version) + 1

        preconditions = await self._precondition_reference_resolver.resolve(
            source.project_key, request.preconditions
        )
        test_case = TestCase(
            identifier=uuid4(),
            project_key=source.project_key,
            test_key=source.test_key,
            version=next_version,
            name=request.name,
            summary=request.summary,
            objective=request.objective,
            test_type=request.test_type,
            test_level=request.test_level,
            priority=request.priority,
            definition=request.definition,
            timeout_seconds=request.timeout_seconds,
            created_at=request.requested_at,
            created_by=request.requested_by,
            preconditions=preconditions,
            metadata=request.metadata,
        )
        return await self._test_case_repository.save(test_case)
