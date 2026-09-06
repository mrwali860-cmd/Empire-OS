from pathlib import Path

import pytest

from src.agent.capabilities import CapabilityError, CapabilityResult, EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus
from src.agent.tasks import Task


def make_task(command="file_read", description="Execute planned step: read file src/app.py"):
    return Task(id="TASK-FILE-001", name="File read", description=description, command=command, requires_permission=False)


def make_plan(action="file_read", description="Execute planned step: read file src/app.py"):
    return {
        "status": "READY",
        "plan_id": "PLAN-FILE-001",
        "goal": "Read project file",
        "tasks": [{"id": "TASK-FILE-001", "title": "Read file", "description": description, "action": action, "requires_permission": False}],
    }


def test_file_read_returns_bounded_content(tmp_path: Path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    target = source_dir / "app.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute("file_read", make_task())
    assert result.ok is True
    assert result.capability == "file_read"
    assert result.data == {
        "path": "src/app.py",
        "content": "print('hello')\n",
        "char_count": 15,
        "truncated": False,
    }


def test_file_read_completed_and_audited(tmp_path: Path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 42\n", encoding="utf-8")
    result = EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)).execute_plan(
        make_plan(description="Execute planned step: read file app.py")
    )
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1
    audit = result["audit"][0]
    assert audit["capability"] == "file_read"
    assert audit["verified"] is True
    assert audit["result"]["data"]["content"] == "VALUE = 42\n"


def test_file_read_input_contract_rejects_empty_path(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    with pytest.raises(CapabilityError, match="Invalid input for capability: file_read"):
        executor.execute("file_read", make_task(description="Execute planned step: read file:"))


def test_file_read_input_contract_accepts_read_and_open_markers(tmp_path: Path):
    target = tmp_path / "app.py"
    target.write_text("OK\n", encoding="utf-8")
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    assert executor.execute("file_read", make_task(description="read file: app.py")).ok is True
    assert executor.execute("file_read", make_task(description="open file app.py")).ok is True


def test_file_read_output_contract_rejects_malformed_result(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    malformed = CapabilityResult(True, "file_read", {"path": "app.py"})
    assert executor.verify("file_read", malformed) is False


def test_file_read_output_contract_rejects_inconsistent_char_count(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    malformed = CapabilityResult(True, "file_read", {"path": "app.py", "content": "abc", "char_count": 2, "truncated": False})
    assert executor.verify("file_read", malformed) is False


def test_file_read_truncation_contract(tmp_path: Path):
    target = tmp_path / "large.txt"
    target.write_text("x" * (EmpireCapabilityExecutor(project_root=tmp_path).registry.get("file_read").handler.__self__.MAX_CHARS + 10), encoding="utf-8")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_read", make_task(description="read file large.txt")
    )
    assert result.ok is True
    assert result.data["truncated"] is True
    assert len(result.data["content"]) == 20_000
    assert result.data["char_count"] == 20_010
    assert EmpireCapabilityExecutor(project_root=tmp_path).verify("file_read", result) is True


def test_file_read_rejects_path_traversal(tmp_path: Path):
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_read", make_task(description="Execute planned step: read file ../secret.txt")
    )
    assert result.ok is False
    assert "outside" in result.error.lower()


def test_file_read_rejects_oversized_file(tmp_path: Path):
    target = tmp_path / "huge.bin"
    with target.open("wb") as handle:
        handle.truncate(1_000_001)
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_read", make_task(description="read file huge.bin")
    )
    assert result.ok is False
    assert "size limit" in result.error.lower()
    assert EmpireCapabilityExecutor(project_root=tmp_path).verify("file_read", result) is False


def test_file_read_rejects_non_utf8(tmp_path: Path):
    target = tmp_path / "binary.dat"
    target.write_bytes(b"\xff\xfe\xfd")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_read", make_task(description="read file binary.dat")
    )
    assert result.ok is False
    assert result.error


def test_file_read_missing_file_fails(tmp_path: Path):
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute("file_read", make_task())
    assert result.ok is False
    assert EmpireCapabilityExecutor(project_root=tmp_path).verify("file_read", result) is False


def test_file_read_unregistered_route_rejected():
    orchestrator = EmpireOrchestrator()
    orchestrator.routes["file_read"] = "missing_file_read"
    result = orchestrator.execute_plan(make_plan())
    assert result["status"] == OrchestrationStatus.REJECTED.value
