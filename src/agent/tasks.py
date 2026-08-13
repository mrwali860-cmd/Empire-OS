"""
Empire OS
Task Engine — v0.1

Purpose:
Represent, track, and manage executable tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Lifecycle states for an Empire OS task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(slots=True)
class Task:
    """A single unit of work for Empire OS."""

    id: str
    name: str
    description: str
    command: str
    requires_permission: bool = True
    status: TaskStatus = TaskStatus.PENDING
    result: Any | None = None
    error: str | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def start(self) -> None:
        """Mark the task as running."""

        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def complete(self, result: Any = None) -> None:
        """Mark the task as completed."""

        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, error: str) -> None:
        """Mark the task as failed."""

        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)

    def reject(self, reason: str | None = None) -> None:
        """Reject the task."""

        self.status = TaskStatus.REJECTED
        self.error = reason
        self.completed_at = datetime.now(timezone.utc)

    def is_finished(self) -> bool:
        """Return whether the task reached a terminal state."""

        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.REJECTED,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the task for APIs, logs, or storage."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "requires_permission": self.requires_permission,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at
                else None
            ),
        }