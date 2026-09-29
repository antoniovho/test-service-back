"""SQLAlchemy DTOs for composed Test Set snapshots."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from test_service.infrastructure.adapters.output.commons.persistence.postgres.base import Base


class TestSetDTO(Base):
    """Database representation of ``test_service_v1.test_set``."""

    __tablename__ = "test_set"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    project_key: Mapped[str] = mapped_column(Text, nullable=False)
    set_key: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    item_links: Mapped[list["TestSetItemDTO"]] = relationship(
        back_populates="test_set",
        cascade="all, delete-orphan",
        order_by="TestSetItemDTO.position",
    )


class TestSetItemDTO(Base):
    """Database representation of ordered Test Set Test Case references."""

    __tablename__ = "test_set_item"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    test_set_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("test_service_v1.test_set.id"), nullable=False
    )
    test_case_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    test_set: Mapped[TestSetDTO] = relationship(back_populates="item_links")
