from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.mappers.precondition_persistence_mapper import (  # noqa: E501
    PreconditionPersistenceMapper,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.precondition_persistence_adapter import (  # noqa: E501
    PreconditionPersistenceAdapter,
)


def _precondition() -> Precondition:
    return Precondition(
        identifier=uuid4(),
        project_key="IAG",
        precondition_key="authenticated",
        version=1,
        name="Authenticated user",
        description="User has a session",
        validation_definition=Definition(
            schema_version="1.0",
            variables={},
            actions=(Action(identifier="session", action_type="CHECK_SESSION", configuration={}),),
        ),
        metadata={},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
    )


class _Repository:
    def __init__(self, precondition: Precondition | None) -> None:
        self.dto = PreconditionPersistenceMapper.to_dto(precondition) if precondition else None
        self.saved = None

    async def save(self, dto):
        self.saved = dto
        return dto

    async def find_by_id(self, _):
        return self.dto

    async def find_latest_version(self, _, __):
        return 4

    async def find_page(self, _, __, ___):
        return Page(
            items=() if self.dto is None else (self.dto,), total=0 if self.dto is None else 1
        )

    async def find_versions(self, _, __, ___, ____):
        return Page(
            items=() if self.dto is None else (self.dto,), total=0 if self.dto is None else 1
        )


class TestPreconditionPersistenceAdapter:
    async def test_when_saving_or_finding_precondition_expect_domain_snapshot(self):
        precondition = _precondition()
        repository = _Repository(precondition)
        adapter = PreconditionPersistenceAdapter(repository)

        saved = await adapter.save(precondition)
        found = await adapter.find_by_id(precondition.identifier)

        assert saved == precondition
        assert found == precondition
        assert repository.saved.id == precondition.identifier

    async def test_when_precondition_is_absent_expect_none(self):
        result = await PreconditionPersistenceAdapter(_Repository(None)).find_by_id(uuid4())

        assert result is None

    async def test_when_versions_and_page_are_requested_expect_mapped_pages(self):
        precondition = _precondition()
        adapter = PreconditionPersistenceAdapter(_Repository(precondition))
        pagination = PaginationParams()

        page = await adapter.find_page("IAG", pagination, VersionStatus.ACTIVE)
        versions = await adapter.find_versions("IAG", "authenticated", pagination)
        latest_version = await adapter.find_latest_version("IAG", "authenticated")

        assert page.items == (precondition,)
        assert versions.items == (precondition,)
        assert latest_version == 4
