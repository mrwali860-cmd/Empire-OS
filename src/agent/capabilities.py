"""Controlled capability layer for Empire OS."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .file_read import FileReadCapability
from .file_write import FileWriteCapability
from .git_status import GitStatusCapability
from .project_search import ProjectSearchCapability
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

    def execute(self, name: str, task: Task) -> CapabilityResult:
        handler = self._handlers.get(name)
        if handler is None:
            raise CapabilityError(f"Capability is not registered: {name}")
        raw = handler(task)
        if isinstance(raw, CapabilityResult):
            return raw
        if isinstance(raw, dict):
            return CapabilityResult(ok=bool(raw.get("ok", False)), capability=str(raw.get("capability", name)), data=raw.get("data") if isinstance(raw.get("data"), dict) else {}, error=raw.get("error"))
        raise CapabilityError(f"Malformed capability result for: {name}")

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))


class EmpireCapabilityExecutor:
    """Concrete, controlled executors used by the Empire orchestrator."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[2])
        self.registry = CapabilityRegistry()
        self.registry.register("file_read", FileReadCapability(self.project_root).execute)
        self.registry.register("file_write", FileWriteCapability(self.project_root).execute)
        self.registry.register("project_inspection", self.inspect_project)
        self.registry.register("project_search", ProjectSearchCapability(self.project_root).execute)
        self.registry.register("test_runner", self.run_tests)
        self.registry.register("git_status", GitStatusCapability(self.project_root).execute)

    def execute(self, capability: str, task: Task) -> CapabilityResult:
        return self.registry.execute(capability, task)

    def verify(self, capability: str, result: Any) -> bool:
        if not isinstance(result, CapabilityResult):
            return False
        if result.capability != capability or not result.ok or result.error is not None:
            return False
        data = result.data or {}
        if capability == "file_read":
            return (isinstance(data.get("path"), str) and bool(data["path"]) and isinstance(data.get("content"), str) and isinstance(data.get("char_count"), int) and data["char_count"] >= len(data["content"]) and isinstance(data.get("truncated"), bool))
        if capability == "file_write":
            return isinstance(data.get("path"), str) and bool(data["path"]) and isinstance(data.get("bytes_written"), int) and 0 <= data["bytes_written"] <= FileWriteCapability.MAX_BYTES
        if capability == "project_inspection":
            return isinstance(data.get("files"), int) and data["files"] >= 0 and isinstance(data.get("directories"), int) and data["directories"] >= 0
        if capability == "project_search":
            matches = data.get("matches")
            return (isinstance(data.get("query"), str) and bool(data["query"].strip()) and isinstance(data.get("match_count"), int) and data["match_count"] == len(matches) if isinstance(matches, list) else False) and (isinstance(matches, list) and len(matches) <= ProjectSearchCapability.MAX_MATCHES and all(isinstance(match, dict) and isinstance(match.get("file"), str) and bool(match["file"]) and isinstance(match.get("line"), int) and match["line"] >= 1 and isinstance(match.get("text"), str) for match in matches) and isinstance(data.get("truncated"), bool))
        if capability == "test_runner":
            return data.get("return_code") == 0
        if capability == "git_status":
            return (isinstance(data.get("branch"), str) and bool(data["branch"]) and isinstance(data.get("clean"), bool) and isinstance(data.get("changed_files"), list) and all(isinstance(path, str) for path in data["changed_files"]) and isinstance(data.get("commit_sha"), str) and len(data["commit_sha"]) == 40)
        return False

    def inspect_project(self, task: Task) -> CapabilityResult:
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
        completed = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=self.project_root, capture_output=True, text=True, check=False, timeout=300)
        return CapabilityResult(ok=completed.returncode == 0, capability="test_runner", data={"return_code": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}, error=f"Test suite failed with exit code {completed.returncode}." if completed.returncode != 0 else None)
