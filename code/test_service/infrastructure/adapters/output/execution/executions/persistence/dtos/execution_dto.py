"""SQLAlchemy DTO for Test Plan executions."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from test_service.infrastructure.adapters.output.commons.persistence.postgres.base import Base


class ExecutionDTO(Base):
    """Database representation of ``test_service_v1.execution``."""

    __tablename__ = "execution"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    project_key: Mapped[str] = mapped_column(Text, nullable=False)
    test_plan_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    environment_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    triggered_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    runner_version: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
