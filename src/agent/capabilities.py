"""Controlled capability layer for Empire OS."""

from __future__ import annotations

import hashlib
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .decision_engine import DecisionEngineCapability
from .file_read import FileReadCapability
from .file_write import FileWriteCapability
from .git_status import GitStatusCapability
from .project_search import ProjectSearchCapability
from .tasks import Task

CapabilityHandler = Callable[[Task], Any]
CapabilityInputValidator = Callable[[Any], bool]
CapabilityVerifier = Callable[["CapabilityResult"], bool]


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


@dataclass(frozen=True, slots=True)
class CapabilityContract:
    """Executable contract for one capability: input, execution, output, verification, evidence."""

    name: str
    handler: CapabilityHandler
    verify: CapabilityVerifier
    validate_input: CapabilityInputValidator = lambda value: isinstance(value, Task)

    def validate(self, task: Any) -> None:
        if not self.validate_input(task):
            raise CapabilityError(f"Invalid input for capability: {self.name}")

    def execute(self, task: Task) -> CapabilityResult:
        self.validate(task)
        raw = self.handler(task)
        if isinstance(raw, CapabilityResult):
            result = raw
        elif isinstance(raw, dict):
            result = CapabilityResult(
                ok=bool(raw.get("ok", False)),
                capability=str(raw.get("capability", self.name)),
                data=raw.get("data") if isinstance(raw.get("data"), dict) else {},
                error=raw.get("error"),
            )
        else:
            raise CapabilityError(f"Malformed capability result for: {self.name}")
        if result.capability != self.name:
            raise CapabilityError(f"Capability result mismatch: expected {self.name}, got {result.capability}")
        return result

    def evidence(self, result: CapabilityResult) -> dict[str, Any]:
        return result.to_dict()

    def verified(self, result: CapabilityResult) -> bool:
        return bool(self.verify(result))


class CapabilityRegistry:
    """Allow-listed registry mapping capability names to executable contracts."""

    def __init__(self) -> None:
        self._contracts: dict[str, CapabilityContract] = {}

    def register(self, name: str, handler: CapabilityHandler, *, verifier: CapabilityVerifier | None = None, input_validator: CapabilityInputValidator | None = None) -> None:
        if not name or not callable(handler):
            raise ValueError("Capability name and callable handler are required.")
        self._contracts[name] = CapabilityContract(name=name, handler=handler, verify=verifier or (lambda result: result.ok and result.error is None), validate_input=input_validator or (lambda value: isinstance(value, Task)))

    def has(self, name: str) -> bool:
        return name in self._contracts

    def get(self, name: str) -> CapabilityContract:
        contract = self._contracts.get(name)
        if contract is None:
            raise CapabilityError(f"Capability is not registered: {name}")
        return contract

    def execute(self, name: str, task: Task) -> CapabilityResult:
        return self.get(name).execute(task)

    def verify(self, name: str, result: Any) -> bool:
        contract = self.get(name)
        if not isinstance(result, CapabilityResult) or result.capability != name:
            return False
        return contract.verified(result)

    def evidence(self, name: str, result: Any) -> dict[str, Any] | None:
        if not isinstance(result, CapabilityResult) or result.capability != name:
            return None
        return self.get(name).evidence(result)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._contracts))


class EmpireCapabilityExecutor:
    """Concrete, controlled executors used by the Empire orchestrator."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parents[2]).resolve()
        self.registry = CapabilityRegistry()
        self.registry.register("file_read", FileReadCapability(self.project_root).execute, verifier=self._verify_file_read, input_validator=FileReadCapability.validate_task)
        self.registry.register("file_write", FileWriteCapability(self.project_root).execute, verifier=self._verify_file_write, input_validator=FileWriteCapability.validate_task)
        self.registry.register("project_inspection", self.inspect_project, verifier=self._verify_project_inspection)
        self.registry.register("project_search", ProjectSearchCapability(self.project_root).execute, verifier=self._verify_project_search)
        self.registry.register("test_runner", self.run_tests, verifier=self._verify_test_runner)
        self.registry.register("git_status", GitStatusCapability(self.project_root).execute, verifier=self._verify_git_status)
        self.decision_engine = DecisionEngineCapability()
        self.registry.register("decision_engine", self.decision_engine.execute, verifier=self._verify_decision_engine, input_validator=DecisionEngineCapability.validate_task)

    def execute(self, capability: str, task: Task) -> CapabilityResult:
        return self.registry.execute(capability, task)

    def verify(self, capability: str, result: Any) -> bool:
        try:
            return self.registry.verify(capability, result)
        except CapabilityError:
            return False

    def _verify_file_read(self, result: CapabilityResult) -> bool:
        data = result.data or {}
        path, content, char_count, truncated = data.get("path"), data.get("content"), data.get("char_count"), data.get("truncated")
        if not (result.ok and result.error is None and isinstance(path, str) and bool(path) and isinstance(content, str) and len(content) <= FileReadCapability.MAX_CHARS and isinstance(char_count, int) and not isinstance(char_count, bool) and char_count >= 0 and char_count >= len(content) and isinstance(truncated, bool) and truncated is (char_count > len(content))):
            return False
        candidate = (self.project_root / path).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError:
            return False
        return candidate.is_file() and not candidate.is_symlink()

    def _verify_file_write(self, result: CapabilityResult) -> bool:
        data = result.data or {}
        if not (result.ok and result.error is None and isinstance(data.get("path"), str) and bool(data["path"]) and isinstance(data.get("bytes_written"), int) and 0 <= data["bytes_written"] <= FileWriteCapability.MAX_BYTES and isinstance(data.get("sha256"), str) and len(data["sha256"]) == 64):
            return False
        candidate = (self.project_root / data["path"]).resolve()
        try:
            candidate.relative_to(self.project_root)
            payload = candidate.read_bytes()
        except (OSError, ValueError):
            return False
        return len(payload) == data["bytes_written"] and hashlib.sha256(payload).hexdigest() == data["sha256"]

    @staticmethod
    def _verify_project_inspection(result: CapabilityResult) -> bool:
        data = result.data or {}
        return (result.ok and result.error is None and isinstance(data.get("project_root"), str) and bool(data["project_root"]) and isinstance(data.get("files"), int) and not isinstance(data["files"], bool) and data["files"] >= 0 and isinstance(data.get("directories"), int) and not isinstance(data["directories"], bool) and data["directories"] >= 0)

    @staticmethod
    def _verify_project_search(result: CapabilityResult) -> bool:
        data = result.data or {}
        matches = data.get("matches")
        return (result.ok and result.error is None and isinstance(data.get("query"), str) and bool(data["query"].strip()) and isinstance(data.get("match_count"), int) and data["match_count"] >= 0 and isinstance(data.get("scanned_files"), int) and data["scanned_files"] >= 0 and isinstance(matches, list) and data["match_count"] == len(matches) and len(matches) <= ProjectSearchCapability.MAX_MATCHES and all(isinstance(match, dict) and isinstance(match.get("file"), str) and bool(match["file"]) and isinstance(match.get("line"), int) and match["line"] >= 1 and isinstance(match.get("text"), str) and len(match["text"]) <= ProjectSearchCapability.MAX_LINE_LENGTH for match in matches) and isinstance(data.get("truncated"), bool))

    @staticmethod
    def _verify_test_runner(result: CapabilityResult) -> bool:
        data = result.data or {}
        return (result.ok and result.error is None and isinstance(data.get("return_code"), int) and not isinstance(data.get("return_code"), bool) and data["return_code"] == 0 and isinstance(data.get("stdout"), str) and len(data["stdout"]) <= 4000 and isinstance(data.get("stderr"), str) and len(data["stderr"]) <= 4000)

    @staticmethod
    def _verify_git_status(result: CapabilityResult) -> bool:
        data = result.data or {}
        return (result.ok and result.error is None and isinstance(data.get("branch"), str) and bool(data["branch"]) and isinstance(data.get("clean"), bool) and isinstance(data.get("changed_files"), list) and all(isinstance(path, str) for path in data["changed_files"]) and isinstance(data.get("commit_sha"), str) and bool(data["commit_sha"]) and len(data["commit_sha"]) == 40 and all(c in "0123456789abcdefABCDEF" for c in data["commit_sha"]))

    @staticmethod
    def _verify_decision_engine(result: CapabilityResult) -> bool:
        data = result.data or {}
        if not (result.ok and result.error is None and result.capability == "decision_engine" and isinstance(data, dict)):
            return False
        if not isinstance(data.get("context"), dict) or not isinstance(data.get("recommended"), dict) or not isinstance(data.get("alternatives"), list) or len(data["alternatives"]) > DecisionEngineCapability.MAX_OPTIONS:
            return False
        recommended = data["recommended"]
        if not EmpireCapabilityExecutor._valid_decision_result(recommended):
            return False
        return all(EmpireCapabilityExecutor._valid_decision_result(item) for item in data["alternatives"])

    @staticmethod
    def _valid_decision_result(value: Any) -> bool:
        if not isinstance(value, dict) or not isinstance(value.get("option"), dict) or not isinstance(value.get("score"), dict):
            return False
        confidence = value.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(float(confidence)) or not 0 <= float(confidence) <= 1:
            return False
        option, score = value["option"], value["score"]
        if not DecisionEngineCapability._valid_option(option):
            return False
        for field in ("roi", "risk", "cost", "execution_time", "complexity", "alignment", "business_impact", "final_score"):
            number = score.get(field)
            if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)):
                return False
        return isinstance(value.get("reasons"), list) and isinstance(value.get("risks"), list) and isinstance(value.get("expected_results"), list)

    def inspect_project(self, task: Task) -> CapabilityResult:
        if not self.project_root.is_dir():
            return CapabilityResult(False, "project_inspection", {}, "Project root does not exist.")
        files = directories = 0
        excluded = {".git", ".pytest_cache", "__pycache__"}
        for path in self.project_root.rglob("*"):
            if any(part in excluded for part in path.parts):
                continue
            if path.is_file(): files += 1
            elif path.is_dir(): directories += 1
        return CapabilityResult(True, "project_inspection", {"project_root": str(self.project_root), "files": files, "directories": directories}, None)

    def run_tests(self, task: Task) -> CapabilityResult:
        completed = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=self.project_root, capture_output=True, text=True, check=False, timeout=300)
        return CapabilityResult(ok=completed.returncode == 0, capability="test_runner", data={"return_code": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}, error=f"Test suite failed with exit code {completed.returncode}." if completed.returncode != 0 else None)
