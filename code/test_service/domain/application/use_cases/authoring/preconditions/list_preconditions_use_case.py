"""Use case implementation: list Preconditions."""

from test_service.domain.application.queries.authoring import ListPreconditionsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_preconditions_use_case import (  # noqa: E501
    ListPreconditionsUseCase,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)


class ListPreconditionsUseCaseImpl(ListPreconditionsUseCase):
    """Lists Precondition snapshots for one project."""

    def __init__(
        self,
        precondition_repository: PreconditionPersistencePort,
        project_resolver: ProjectResolver,
    ) -> None:
        self._precondition_repository = precondition_repository
        self._project_resolver = project_resolver

    async def execute(self, request: ListPreconditionsQuery) -> Page[Precondition]:
        await self._project_resolver.resolve(request.project_key)
        return await self._precondition_repository.find_page(
            request.project_key, request.pagination, request.status
        )
