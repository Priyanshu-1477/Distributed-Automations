import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class WorkerStatus(StrEnum):
    """Application-level worker liveness status."""

    STARTING = "STARTING"
    HEALTHY = "HEALTHY"
    STALE = "STALE"
    OFFLINE = "OFFLINE"


class WorkerRecord(Base, TimestampMixin):
    """Persistent registry of worker instances and health telemetry."""

    __tablename__ = "workers"

    worker_id: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
    )
    hostname: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    pid: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=WorkerStatus.STARTING.value,
        nullable=False,
        index=True,
    )
    capabilities: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    concurrency: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    last_heartbeat_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
        index=True,
    )
    registered_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
