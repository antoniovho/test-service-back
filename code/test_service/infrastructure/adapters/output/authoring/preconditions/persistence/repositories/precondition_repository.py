"""SQLAlchemy repository for Precondition DTOs."""

from uuid import UUID

from sqlalchemy import select

from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)


class PreconditionRepository:
    """Retrieve Precondition DTOs required by Test Case authoring."""

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def find_by_id(self, identifier: UUID) -> PreconditionDTO | None:
        """Find one Precondition snapshot by UUID."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(PreconditionDTO).where(PreconditionDTO.id == identifier)
            )
            return result.scalar_one_or_none()
