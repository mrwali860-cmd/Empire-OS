"""Execution audit contracts for Empire OS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Immutable evidence record for one orchestrated task."""

    task_id: str
    command: str
    capability: str
    status: str
    verified: bool
    error: str | None = None
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "command": self.command,
            "capability": self.capability,
            "status": self.status,
            "verified": self.verified,
            "error": self.error,
            "result": self.result or {},
        }


class ExecutionAudit:
    """Small in-memory audit trail for the current execution."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def record(self, record: AuditRecord) -> None:
        self._records.append(record)

    def clear(self) -> None:
        self._records.clear()

    @property
    def records(self) -> tuple[AuditRecord, ...]:
        return tuple(self._records)

    def as_dicts(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self._records]
