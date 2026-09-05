from pathlib import Path

import pytest

from src.agent.capabilities import CapabilityError, CapabilityRegistry, CapabilityResult, EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus
from src.agent.tasks import Task


def make_task(command="inspect_project"):
    return Task(id="TASK-001", name="Capability test", description="Test capability execution", command=command, requires_permission=False)


def make_plan(action="inspect_project"):
    return {"status": "READY", "plan_id": "PLAN-CAP-001", "goal": "Capability verification", "tasks": [{"id": "TASK-001", "title": "Capability", "description": "Test", "action": action, "requires_permission": False}]}


def test_capability_result_contract_serializes():
    result = CapabilityResult(ok=True, capability="project_inspection", data={"files": 2, "directories": 1})
    assert result.to_dict()["ok"] is True
    assert result.to_dict()["capability"] == "project_inspection"


def test_registry_executes_registered_capability():
    registry = CapabilityRegistry()
    calls = []
    registry.register("demo", lambda task: calls.append(task.id) or {"ok": True})
    result = registry.execute("demo", make_task())
    assert isinstance(result, CapabilityResult)
    assert result.ok is True
    assert result.capability == "demo"
    assert calls == ["TASK-001"]


def test_registry_rejects_unknown_capability():
    with pytest.raises(CapabilityError, match="not registered"):
        CapabilityRegistry().execute("missing", make_task())


def test_default_executor_registers_real_routes(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    assert executor.registry.names == ("git_status", "project_inspection", "test_runner")
    result = executor.execute("project_inspection", make_task())
    assert isinstance(result, CapabilityResult)
    assert result.ok is True
    assert result.capability == "project_inspection"


def test_inspection_is_read_only(tmp_path: Path):
    (tmp_path / "sample.txt").write_text("hello", encoding="utf-8")
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = executor.inspect_project(make_task())
    assert result.data["files"] == 1
    assert (tmp_path / "sample.txt").read_text(encoding="utf-8") == "hello"


def test_successful_inspection_completed(tmp_path: Path):
    result = EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)).execute_plan(make_plan("inspect_project"))
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1


def test_passing_tests_completed(monkeypatch, tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)

    class Completed:
        returncode = 0
        stdout = "1 passed"
        stderr = ""

    monkeypatch.setattr("src.agent.capabilities.subprocess.run", lambda *args, **kwargs: Completed())
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


def test_unknown_capability_rejected():
    result = EmpireOrchestrator(EmpireCapabilityExecutor()).execute_plan(make_plan("unknown_command"))
    assert result["status"] == OrchestrationStatus.REJECTED.value


def test_unregistered_capability_route_rejected():
    orchestrator = EmpireOrchestrator(EmpireCapabilityExecutor())
    orchestrator.routes["inspect_project"] = "missing_capability"
    result = orchestrator.execute_plan(make_plan("inspect_project"))
    assert result["status"] == OrchestrationStatus.REJECTED.value
    assert result["failed_task_id"] == "TASK-001"


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


def test_git_status_returns_read_only_evidence():
    executor = EmpireCapabilityExecutor()
    result = executor.execute("git_status", make_task("git_status"))
    assert result.ok is True
    assert result.capability == "git_status"
    assert isinstance(result.data["branch"], str)
    assert isinstance(result.data["clean"], bool)
    assert isinstance(result.data["changed_files"], list)
    assert len(result.data["commit_sha"]) == 40


def test_git_status_completed_and_audited():
    result = EmpireOrchestrator(EmpireCapabilityExecutor()).execute_plan(make_plan("git_status"))
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1
    audit = result["audit"][0]
    assert audit["capability"] == "git_status"
    assert audit["status"] == "completed"
    assert audit["verified"] is True
    assert audit["result"]["data"]["commit_sha"]


def test_git_status_malformed_result_failed():
    class MalformedExecutor(EmpireCapabilityExecutor):
        def execute(self, capability, task):
            if capability == "git_status":
                return CapabilityResult(ok=True, capability="git_status", data={"branch": "main"})
            return super().execute(capability, task)

    result = EmpireOrchestrator(MalformedExecutor()).execute_plan(make_plan("git_status"))
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["failed_task_id"] == "TASK-001"
    assert result["audit"][0]["verified"] is False
