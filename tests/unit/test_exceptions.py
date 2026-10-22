import uuid

from src.core.exceptions import (
    DispatchError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    OptimisticLockError,
)


def test_entity_not_found_error():
    task_id = uuid.uuid4()
    exc = EntityNotFoundError("Task", task_id)
    assert f"Task with id '{task_id}' was not found." in str(exc)
    assert exc.details["entity_name"] == "Task"
    assert exc.details["entity_id"] == str(task_id)


def test_invalid_state_transition_error():
    exc = InvalidStateTransitionError("Task", "SUCCEEDED", "RUNNING")
    assert "Cannot transition Task from 'SUCCEEDED' to 'RUNNING'." in str(exc)
    assert exc.details["current_state"] == "SUCCEEDED"
    assert exc.details["target_state"] == "RUNNING"


def test_optimistic_lock_error():
    task_id = uuid.uuid4()
    exc = OptimisticLockError("Task", task_id, expected_version=2)
    assert f"Optimistic lock conflict on Task '{task_id}'" in str(exc)
    assert exc.details["expected_version"] == 2


def test_dispatch_error():
    task_id = uuid.uuid4()
    exc = DispatchError(task_id, "Redis connection timed out")
    assert "Failed to dispatch task" in str(exc)
    assert exc.details["broker_error"] == "Redis connection timed out"
