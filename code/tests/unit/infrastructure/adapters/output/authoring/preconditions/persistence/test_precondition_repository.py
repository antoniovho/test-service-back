from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.repositories.precondition_repository import (  # noqa: E501
    PreconditionRepository,
)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


class TestPreconditionRepository:
    async def test_when_precondition_exists_expect_dto_returned(self):
        dto = PreconditionDTO(
            id=uuid4(),
            project_key="IAG",
            precondition_key="authenticated",
            version=1,
            name="Authenticated user",
            description="User has a session",
            validation_definition={"schema_version": "1.0", "variables": {}, "actions": []},
            status="DRAFT",
            metadata_={},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="author@example.test",
        )
        result = MagicMock()
        result.scalar_one_or_none.return_value = dto
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        found = await PreconditionRepository(_SessionProvider(session)).find_by_id(dto.id)

        assert found is dto
        session.execute.assert_awaited_once()

    async def test_when_precondition_is_absent_expect_none(self):
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)

        found = await PreconditionRepository(_SessionProvider(session)).find_by_id(uuid4())

        assert found is None
