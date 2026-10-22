"""Initial schema: tasks, task_execution_attempts, workers

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-22 10:50:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create 'tasks' table
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("cancellation_requested", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_task_type"), "tasks", ["task_type"], unique=False)

    # 2. Create 'task_execution_attempts' table
    op.create_table(
        "task_execution_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=False),
        sa.Column("celery_task_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_traceback", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "attempt_number", name="uq_task_attempt_number"),
    )
    op.create_index(
        op.f("ix_task_execution_attempts_task_id"),
        "task_execution_attempts",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_execution_attempts_worker_id"),
        "task_execution_attempts",
        ["worker_id"],
        unique=False,
    )

    # 3. Create 'workers' table
    op.create_table(
        "workers",
        sa.Column("worker_id", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("pid", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("concurrency", sa.Integer(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("worker_id"),
    )
    op.create_index(
        op.f("ix_workers_last_heartbeat_at"),
        "workers",
        ["last_heartbeat_at"],
        unique=False,
    )
    op.create_index(op.f("ix_workers_status"), "workers", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workers_status"), table_name="workers")
    op.drop_index(op.f("ix_workers_last_heartbeat_at"), table_name="workers")
    op.drop_table("workers")

    op.drop_index(
        op.f("ix_task_execution_attempts_worker_id"),
        table_name="task_execution_attempts",
    )
    op.drop_index(
        op.f("ix_task_execution_attempts_task_id"),
        table_name="task_execution_attempts",
    )
    op.drop_table("task_execution_attempts")

    op.drop_index(op.f("ix_tasks_task_type"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_table("tasks")
