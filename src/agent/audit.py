"""Execution audit contracts for Empire OS."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


_ALLOWED_STATUSES = frozenset({"ready", "running", "verifying", "completed", "failed", "rejected"})
_MAX_RESULT_CHARS = 4_000
_UNSAFE_KEYS = frozenset({"api_key", "access_token", "authorization", "password", "secret", "token"})


def _validate_result(value: dict[str, Any] | None) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise TypeError("result must be a dictionary")
    try:
        serialized = json.dumps(value, sort_keys=True, default=str)
    except (TypeError, ValueError) as exc:
        raise ValueError("result must be safely serializable") from exc
    if len(serialized) > _MAX_RESULT_CHARS:
        raise ValueError("result is too large")
    for key in value:
        if isinstance(key, str) and key.strip().lower() in _UNSAFE_KEYS:
            raise ValueError("result contains unsafe key")


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
    request_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str):
            raise TypeError("task_id must be a string")
        if not self.task_id.strip():
            raise ValueError("task_id must be non-empty")
        if not isinstance(self.command, str):
            raise TypeError("command must be a string")
        if not self.command.strip():
            raise ValueError("command must be non-empty")
        if not isinstance(self.capability, str):
            raise TypeError("capability must be a string")
        if not self.capability.strip():
            raise ValueError("capability must be non-empty")
        if not isinstance(self.status, str) or self.status.strip().lower() not in _ALLOWED_STATUSES:
            raise ValueError("status is invalid")
        if type(self.verified) is not bool:
            raise TypeError("verified must be a bool")
        if self.error is not None and not isinstance(self.error, str):
            raise TypeError("error must be a string or None")
        if self.request_id is not None:
            if not isinstance(self.request_id, str):
                raise TypeError("request_id must be a string or None")
            if not self.request_id.strip():
                raise ValueError("request_id must be non-empty when provided")
            if len(self.request_id) > 200:
                raise ValueError("request_id exceeds 200 characters")
        _validate_result(self.result)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
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
