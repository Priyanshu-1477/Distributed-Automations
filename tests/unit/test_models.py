import datetime
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    AttemptStatus,
    TaskExecutionAttempt,
    TaskRecord,
    TaskStatus,
    WorkerRecord,
    WorkerStatus,
)


@pytest.mark.asyncio
async def test_create_task_record(db_session: AsyncSession):
    """Verify task model creation with default values and versioning."""
    task = TaskRecord(
        task_type="compute.prime_factorization",
        payload={"n": 100},
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert isinstance(task.id, uuid.UUID)
    assert task.status == TaskStatus.QUEUED.value
    assert task.version == 1
    assert task.retry_count == 0
    assert task.max_retries == 3
    assert task.cancellation_requested is False
    assert task.created_at is not None
    assert task.updated_at is not None


@pytest.mark.asyncio
async def test_task_attempt_relationship_and_uniqueness(db_session: AsyncSession):
    """Verify task execution attempt association and attempt number uniqueness."""
    task = TaskRecord(
        task_type="delayed.sleep_and_echo",
        payload={"delay_seconds": 2},
    )
    db_session.add(task)
    await db_session.commit()

    attempt1 = TaskExecutionAttempt(
        task_id=task.id,
        attempt_number=1,
        worker_id="worker-node-1",
        status=AttemptStatus.RUNNING.value,
        started_at=datetime.datetime.now(datetime.UTC),
    )
    db_session.add(attempt1)
    await db_session.commit()

    # Query task with attempts
    result = await db_session.execute(select(TaskRecord).where(TaskRecord.id == task.id))
    loaded_task = result.scalar_one()
    assert loaded_task.id == task.id
    # Eagerly load or query attempts
    attempts_result = await db_session.execute(
        select(TaskExecutionAttempt).where(TaskExecutionAttempt.task_id == task.id)
    )
    attempts = attempts_result.scalars().all()
    assert len(attempts) == 1
    assert attempts[0].attempt_number == 1
    assert attempts[0].worker_id == "worker-node-1"

    # Attempting to insert a duplicate attempt_number for the same task must violate UniqueConstraint
    duplicate_attempt = TaskExecutionAttempt(
        task_id=task.id,
        attempt_number=1,
        worker_id="worker-node-2",
        status=AttemptStatus.RUNNING.value,
        started_at=datetime.datetime.now(datetime.UTC),
    )
    db_session.add(duplicate_attempt)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_create_worker_record(db_session: AsyncSession):
    """Verify worker registration persistence and attributes."""
    worker = WorkerRecord(
        worker_id="worker-local-1",
        hostname="localhost",
        pid=12345,
        status=WorkerStatus.HEALTHY.value,
        capabilities=["compute", "delayed", "failing"],
        concurrency=4,
    )
    db_session.add(worker)
    await db_session.commit()

    result = await db_session.execute(
        select(WorkerRecord).where(WorkerRecord.worker_id == "worker-local-1")
    )
    loaded_worker = result.scalar_one()
    assert loaded_worker.hostname == "localhost"
    assert loaded_worker.concurrency == 4
    assert "compute" in loaded_worker.capabilities
    assert loaded_worker.status == WorkerStatus.HEALTHY.value
