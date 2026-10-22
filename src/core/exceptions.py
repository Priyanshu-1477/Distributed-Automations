from typing import Any


class DomainError(Exception):
    """Base exception for all domain and business logic errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(DomainError):
    """Raised when a requested domain entity (task, worker, attempt) does not exist."""

    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' was not found.",
            details={"entity_name": entity_name, "entity_id": str(entity_id)},
        )


class InvalidStateTransitionError(DomainError):
    """Raised when an illegal state machine transition is attempted."""

    def __init__(self, entity: str, current_state: str, target_state: str):
        super().__init__(
            message=f"Cannot transition {entity} from '{current_state}' to '{target_state}'.",
            details={
                "entity": entity,
                "current_state": current_state,
                "target_state": target_state,
            },
        )


class OptimisticLockError(DomainError):
    """Raised when a concurrent update conflicts with the current entity version."""

    def __init__(self, entity: str, entity_id: Any, expected_version: int):
        super().__init__(
            message=(
                f"Optimistic lock conflict on {entity} '{entity_id}'. "
                f"Expected version {expected_version}, but entity was modified concurrently."
            ),
            details={
                "entity": entity,
                "entity_id": str(entity_id),
                "expected_version": expected_version,
            },
        )


class DispatchError(DomainError):
    """Raised when dispatching a task to the message broker fails."""

    def __init__(self, task_id: Any, broker_error: str):
        super().__init__(
            message=f"Failed to dispatch task '{task_id}' to broker: {broker_error}",
            details={"task_id": str(task_id), "broker_error": broker_error},
        )
