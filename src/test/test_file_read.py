from pathlib import Path

from src.agent.capabilities import CapabilityResult, EmpireCapabilityExecutor
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


def test_file_read_rejects_path_traversal(tmp_path: Path):
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_read", make_task(description="Execute planned step: read file ../secret.txt")
    )
    assert result.ok is False
    assert "outside" in result.error.lower()


def test_file_read_missing_file_fails(tmp_path: Path):
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute("file_read", make_task())
    assert result.ok is False
    assert EmpireCapabilityExecutor(project_root=tmp_path).verify("file_read", result) is False


def test_file_read_malformed_result_fails(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    malformed = CapabilityResult(True, "file_read", {"path": "app.py"})
    assert executor.verify("file_read", malformed) is False


def test_file_read_unregistered_route_rejected():
    orchestrator = EmpireOrchestrator()
    orchestrator.routes["file_read"] = "missing_file_read"
    result = orchestrator.execute_plan(make_plan())
    assert result["status"] == OrchestrationStatus.REJECTED.value
