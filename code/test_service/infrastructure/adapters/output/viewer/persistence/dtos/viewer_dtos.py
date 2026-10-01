"""SQLAlchemy DTOs for Viewer synchronization state."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from test_service.infrastructure.adapters.output.commons.persistence.postgres.base import Base


class ViewerSyncRecordDTO(Base):
    __tablename__ = "viewer_sync_record"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    project_key: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_key: Mapped[str] = mapped_column(Text, nullable=False)
    projected_version_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    viewer_type: Mapped[str] = mapped_column(String, nullable=False)
    external_entity_key: Mapped[str] = mapped_column(Text, nullable=False)
    external_entity_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_status: Mapped[str] = mapped_column(String, nullable=False)
    operation_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ViewerOperationDTO(Base):
    __tablename__ = "viewer_operation"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    project_key: Mapped[str] = mapped_column(Text, nullable=False)
    viewer_type: Mapped[str] = mapped_column(String, nullable=False)
    operation_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_items: Mapped[int | None] = mapped_column(nullable=True)
    succeeded_items: Mapped[int | None] = mapped_column(nullable=True)
    failed_items: Mapped[int | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class DriftEventDTO(Base):
    __tablename__ = "drift_event"
    __table_args__ = {"schema": "test_service_v1"}

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    project_key: Mapped[str] = mapped_column(Text, nullable=False)
    sync_record_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    projected_version_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    drift_type: Mapped[str] = mapped_column(String, nullable=False)
    notification_status: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
