"""SQLAlchemy DTOs for composed Test Plan snapshots."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from test_service.infrastructure.adapters.output.commons.persistence.postgres.base import Base


class TestPlanDTO(Base):
    """Database representation of ``test_service_v1.test_plan``."""

    __tablename__ = "test_plan"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    project_key: Mapped[str] = mapped_column(Text, nullable=False)
    plan_key: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    test_set_links: Mapped[list["TestPlanTestSetDTO"]] = relationship(
        back_populates="test_plan", cascade="all, delete-orphan"
    )
    test_case_links: Mapped[list["TestPlanTestCaseDTO"]] = relationship(
        back_populates="test_plan", cascade="all, delete-orphan"
    )
    exclusion_links: Mapped[list["TestPlanExclusionDTO"]] = relationship(
        back_populates="test_plan", cascade="all, delete-orphan"
    )


class TestPlanTestSetDTO(Base):
    """Database representation of Test Plan Test Set references."""

    __tablename__ = "test_plan_test_set"
    __table_args__ = {"schema": "test_service_v1"}

    test_plan_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("test_service_v1.test_plan.id"), primary_key=True
    )
    test_set_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    test_plan: Mapped[TestPlanDTO] = relationship(back_populates="test_set_links")


class TestPlanTestCaseDTO(Base):
    """Database representation of direct Test Plan Test Case references."""

    __tablename__ = "test_plan_test_case"
    __table_args__ = {"schema": "test_service_v1"}

    test_plan_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("test_service_v1.test_plan.id"), primary_key=True
    )
    test_case_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    test_plan: Mapped[TestPlanDTO] = relationship(back_populates="test_case_links")


class TestPlanExclusionDTO(Base):
    """Database representation of Test Plan Test Case exclusions."""

    __tablename__ = "test_plan_exclusion"
    __table_args__ = {"schema": "test_service_v1"}

    test_plan_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("test_service_v1.test_plan.id"), primary_key=True
    )
    test_case_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    test_plan: Mapped[TestPlanDTO] = relationship(back_populates="exclusion_links")
