"""Use case implementation: create Test Case."""

from uuid import uuid4

from test_service.domain.application.commands.authoring import CreateTestCaseCommand
from test_service.domain.application.services.resolvers.precondition_reference_resolver import (
    PreconditionReferenceResolver,
)
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.exceptions.test_case_already_exists_exception import (
    TestCaseAlreadyExistsException,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class CreateTestCaseUseCaseImpl(CreateTestCaseUseCase):
    """Creates the first draft snapshot of a Test Case."""

    def __init__(
        self,
        test_case_repository: TestCasePersistencePort,
        precondition_reference_resolver: PreconditionReferenceResolver,
        project_resolver: ProjectResolver,
    ) -> None:
        self._test_case_repository = test_case_repository
        self._precondition_reference_resolver = precondition_reference_resolver
        self._project_resolver = project_resolver

    async def execute(self, request: CreateTestCaseCommand) -> TestCase:
        """Create and persist version one of a Test Case."""
        await self._project_resolver.resolve_active(request.project_key)
        latest_version = await self._test_case_repository.find_latest_version(
            request.project_key, request.test_key
        )
        if latest_version is not None:
            raise TestCaseAlreadyExistsException(request.project_key, request.test_key)
        preconditions = await self._precondition_reference_resolver.resolve(
            request.project_key, request.preconditions
        )
        test_case = TestCase(
            identifier=uuid4(),
            project_key=request.project_key,
            test_key=request.test_key,
            version=1,
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
