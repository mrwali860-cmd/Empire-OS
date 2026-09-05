from pathlib import Path

import pytest

from src.agent.capabilities import CapabilityError, CapabilityRegistry, CapabilityResult, EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus
from src.agent.tasks import Task


def make_task(command="inspect_project"):
    return Task(id="TASK-001", name="Capability test", description="Test capability execution", command=command, requires_permission=False)


def make_plan(action="inspect_project"):
    return {
        "status": "READY",
        "plan_id": "PLAN-CAP-001",
        "goal": "Capability verification",
        "tasks": [{"id": "TASK-001", "title": "Capability", "description": "Test", "action": action, "requires_permission": False}],
    }


def test_capability_result_contract_serializes():
    result = CapabilityResult(ok=True, capability="project_inspection", data={"files": 2, "directories": 1})
    assert result.to_dict()["ok"] is True
    assert result.to_dict()["capability"] == "project_inspection"


def test_registry_executes_registered_capability():
    registry = CapabilityRegistry()
    registry.register("demo", lambda task: {"ok": True})
    result = registry.execute("demo", make_task())
    assert isinstance(result, CapabilityResult)
    assert result.ok is True


def test_registry_rejects_unknown_capability():
    with pytest.raises(CapabilityError, match="not registered"):
        CapabilityRegistry().execute("missing", make_task())


def test_successful_inspection_completed(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = EmpireOrchestrator(executor).execute_plan(make_plan("inspect_project"))
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1


def test_inspection_result_is_standardized(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = executor.inspect_project(make_task())
    assert isinstance(result, CapabilityResult)
    assert result.capability == "project_inspection"
    assert result.data["files"] == 0
    assert executor.verify("project_inspection", result) is True


def test_passing_tests_completed():
    executor = EmpireCapabilityExecutor(project_root=Path(__file__).resolve().parents[2])
    result = EmpireOrchestrator(executor).execute_plan(make_plan("run_tests"))
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1


def test_failing_tests_failed(monkeypatch, tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)

    class Completed:
        returncode = 1
        stdout = "failed"
        stderr = "failure"

    monkeypatch.setattr("src.agent.capabilities.subprocess.run", lambda *args, **kwargs: Completed())
    result = EmpireOrchestrator(executor).execute_plan(make_plan("run_tests"))
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["failed_task_id"] == "TASK-001"


def test_unknown_capability_rejected():
    plan = make_plan("unknown_command")
    result = EmpireOrchestrator(EmpireCapabilityExecutor()).execute_plan(plan)
    assert result["status"] == OrchestrationStatus.REJECTED.value


def test_malformed_capability_result_failed():
    class MalformedExecutor(EmpireCapabilityExecutor):
        def execute(self, capability, task):
            return "not-a-capability-result"

    result = EmpireOrchestrator(MalformedExecutor()).execute_plan(make_plan("inspect_project"))
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["failed_task_id"] == "TASK-001"


def test_capability_verifier_rejects_wrong_capability(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(ok=True, capability="test_runner", data={"return_code": 0})
    assert executor.verify("project_inspection", result) is False
