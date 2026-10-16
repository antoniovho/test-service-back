"""Use case implementation: restore a historical Test Case."""

from uuid import uuid4

from test_service.domain.application.commands.authoring import RestoreTestCaseCommand
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.input.use_cases.authoring.test_cases.restore_test_case_use_case import (  # noqa: E501
    RestoreTestCaseUseCase,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)


class RestoreTestCaseUseCaseImpl(RestoreTestCaseUseCase):
    """Clone a deprecated Test Case snapshot into the next draft version."""

    def __init__(
        self, repository: TestCasePersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._repository = repository
        self._project_resolver = project_resolver

    async def execute(self, request: RestoreTestCaseCommand) -> TestCase:
        await self._project_resolver.resolve_active(request.project_key)
        source = await self._repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test case", str(request.source_id), f"project '{request.project_key}'"
            )
        if source.status is not VersionStatus.DEPRECATED:
            raise InvalidLifecycleTransitionException(
                "only deprecated test case snapshots can be restored"
            )
        latest = await self._repository.find_latest_version(source.project_key, source.test_key)
        return await self._repository.save(
            TestCase(
                identifier=uuid4(),
                project_key=source.project_key,
                test_key=source.test_key,
                version=(latest or source.version) + 1,
                name=source.name,
                summary=source.summary,
                objective=source.objective,
                test_type=source.test_type,
                test_level=source.test_level,
                priority=source.priority,
                definition=source.definition,
                timeout_seconds=source.timeout_seconds,
                created_at=request.requested_at,
                created_by=request.requested_by,
                preconditions=source.preconditions,
                metadata=dict(source.metadata) if source.metadata is not None else None,
            )
        )
