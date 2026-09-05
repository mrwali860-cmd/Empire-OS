from pathlib import Path

import pytest

from src.agent.capabilities import CapabilityError, CapabilityRegistry, EmpireCapabilityExecutor
from src.agent.tasks import Task


def make_task(command="inspect_project"):
    return Task(
        id="TASK-001",
        name="Capability test",
        description="Test capability execution",
        command=command,
        requires_permission=False,
    )


def test_registry_executes_registered_capability():
    registry = CapabilityRegistry()
    calls = []
    registry.register("demo", lambda task: calls.append(task.id) or {"ok": True})

    result = registry.execute("demo", make_task())

    assert result == {"ok": True}
    assert calls == ["TASK-001"]


def test_registry_rejects_unknown_capability():
    with pytest.raises(CapabilityError, match="not registered"):
        CapabilityRegistry().execute("missing", make_task())


def test_default_executor_registers_real_routes(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)

    assert executor.registry.names == ("project_inspection", "test_runner")

    result = executor.execute("project_inspection", make_task())

    assert result["ok"] is True
    assert result["capability"] == "project_inspection"


def test_inspection_is_read_only(tmp_path: Path):
    (tmp_path / "sample.txt").write_text("hello", encoding="utf-8")
    executor = EmpireCapabilityExecutor(project_root=tmp_path)

    result = executor.inspect_project(make_task())

    assert result["files"] == 1
    assert (tmp_path / "sample.txt").read_text(encoding="utf-8") == "hello"


def test_orchestrator_can_execute_registered_capability(tmp_path: Path):
    from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus

    plan = {
        "status": "READY",
        "plan_id": "PLAN-CAP-001",
        "goal": "Inspect project",
        "tasks": [
            {
                "id": "TASK-001",
                "title": "Inspect project",
                "description": "Inspect the project",
                "action": "inspect_project",
                "requires_permission": False,
                "verification": "Inspection succeeds.",
                "status": "PENDING",
            }
        ],
    }

    orchestrator = EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path))
    result = orchestrator.execute_plan(plan)

    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1
