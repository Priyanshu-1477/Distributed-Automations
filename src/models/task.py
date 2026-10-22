import datetime
import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, VersionMixin


class TaskStatus(StrEnum):
    """Authoritative task lifecycle states."""

    QUEUED = "QUEUED"
    DISPATCH_FAILED = "DISPATCH_FAILED"
    RUNNING = "RUNNING"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AttemptStatus(StrEnum):
    """Lifecycle state of an individual task execution attempt."""

    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


class TaskRecord(Base, TimestampMixin, VersionMixin):
    """Authoritative persistent record of a task."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    task_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=TaskStatus.QUEUED.value,
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )
    cancellation_requested: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    attempts: Mapped[list["TaskExecutionAttempt"]] = relationship(
        "TaskExecutionAttempt",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskExecutionAttempt.attempt_number",
    )


class TaskExecutionAttempt(Base, TimestampMixin):
    """Immutable execution attempt record providing per-attempt audit history."""

    __tablename__ = "task_execution_attempts"
    __table_args__ = (UniqueConstraint("task_id", "attempt_number", name="uq_task_attempt_number"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    worker_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=AttemptStatus.RUNNING.value,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_traceback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Relationships
    task: Mapped["TaskRecord"] = relationship(
        "TaskRecord",
        back_populates="attempts",
    )
