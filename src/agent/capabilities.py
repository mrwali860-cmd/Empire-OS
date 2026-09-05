"""Controlled capability layer for Empire OS."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .tasks import Task

CapabilityHandler = Callable[[Task], Any]


class CapabilityError(RuntimeError):
    """Raised when a capability cannot be executed safely."""


@dataclass(frozen=True, slots=True)
class CapabilityResult:
    """Standard result contract returned by concrete capabilities."""

    ok: bool
    capability: str
    data: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "capability": self.capability, "data": self.data or {}, "error": self.error}


class CapabilityRegistry:
    """Allow-listed registry mapping capability names to handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, CapabilityHandler] = {}

    def register(self, name: str, handler: CapabilityHandler) -> None:
        if not name or not callable(handler):
            raise ValueError("Capability name and callable handler are required.")
        self._handlers[name] = handler

    def has(self, name: str) -> bool:
        return name in self._handlers

    def execute(self, name: str, task: Task) -> Any:
        handler = self._handlers.get(name)
        if handler is None:
            raise CapabilityError(f"Capability is not registered: {name}")
        return handler(task)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))


class EmpireCapabilityExecutor:
    """Concrete, controlled executors used by the Empire orchestrator."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[2])
        self.registry = CapabilityRegistry()
        self.registry.register("project_inspection", self.inspect_project)
        self.registry.register("test_runner", self.run_tests)

    def execute(self, capability: str, task: Task) -> Any:
        return self.registry.execute(capability, task)

    def verify(self, capability: str, result: Any) -> bool:
        if not isinstance(result, CapabilityResult):
            return False
        if result.capability != capability or not result.ok or result.error is not None:
            return False
        data = result.data or {}
        if capability == "project_inspection":
            return isinstance(data.get("files"), int) and data["files"] >= 0 and isinstance(data.get("directories"), int) and data["directories"] >= 0
        if capability == "test_runner":
            return data.get("return_code") == 0
        return False

    def inspect_project(self, task: Task) -> CapabilityResult:
        """Return bounded project metadata without modifying the filesystem."""
        if not self.project_root.is_dir():
            raise CapabilityError(f"Project root does not exist: {self.project_root}")
        files = 0
        directories = 0
        for path in self.project_root.rglob("*"):
            if any(part in {".git", ".pytest_cache", "__pycache__"} for part in path.parts):
                continue
            if path.is_file():
                files += 1
            elif path.is_dir():
                directories += 1
        return CapabilityResult(True, "project_inspection", {"project_root": str(self.project_root), "files": files, "directories": directories})

    def run_tests(self, task: Task) -> CapabilityResult:
        """Run pytest with a fixed command; task text cannot alter execution."""
        completed = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=self.project_root, capture_output=True, text=True, check=False, timeout=300)
        return CapabilityResult(
            ok=completed.returncode == 0,
            capability="test_runner",
            data={"return_code": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]},
            error=f"Test suite failed with exit code {completed.returncode}." if completed.returncode != 0 else None,
        )
