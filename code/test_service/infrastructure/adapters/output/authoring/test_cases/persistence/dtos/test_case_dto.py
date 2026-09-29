"""SQLAlchemy DTOs for authored Test Case snapshots."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.base import Base


class TestCaseDTO(Base):
    """Database representation of ``test_service_v1.test_case``."""

    __tablename__ = "test_case"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    project_key: Mapped[str] = mapped_column(Text, nullable=False)
    test_key: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    test_type: Mapped[str] = mapped_column(String, nullable=False)
    test_level: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    precondition_links: Mapped[list["TestCasePreconditionDTO"]] = relationship(
        back_populates="test_case",
        cascade="all, delete-orphan",
        order_by="TestCasePreconditionDTO.position",
    )


class TestCasePreconditionDTO(Base):
    """Database representation of ordered Test Case precondition references."""

    __tablename__ = "test_case_precondition"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    test_case_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("test_service_v1.test_case.id"), nullable=False
    )
    precondition_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("test_service_v1.precondition.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    test_case: Mapped[TestCaseDTO] = relationship(back_populates="precondition_links")
    precondition: Mapped[PreconditionDTO] = relationship()
