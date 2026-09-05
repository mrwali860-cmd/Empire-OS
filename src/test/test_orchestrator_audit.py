from pathlib import Path

from src.agent.capabilities import EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus


def plan(action="inspect_project"):
    return {
        "status": "READY",
        "plan_id": "PLAN-AUDIT-001",
        "goal": "Audit execution",
        "tasks": [{
            "id": "TASK-001",
            "title": "Capability",
            "description": "Audit capability execution",
            "action": action,
            "requires_permission": False,
        }],
    }


def test_successful_capability_creates_completed_audit(tmp_path: Path):
    result = EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)).execute_plan(plan())

    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert len(result["audit"]) == 1
    assert result["audit"][0]["status"] == "completed"
    assert result["audit"][0]["verified"] is True
    assert result["audit"][0]["capability"] == "project_inspection"


def test_failing_capability_creates_failed_audit(monkeypatch, tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)

    class Completed:
        returncode = 1
        stdout = "failed"
        stderr = "failure"

    monkeypatch.setattr("src.agent.capabilities.subprocess.run", lambda *args, **kwargs: Completed())
    result = EmpireOrchestrator(executor).execute_plan(plan("run_tests"))

    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["audit"][0]["status"] == "failed"
    assert result["audit"][0]["verified"] is False


def test_unknown_command_creates_rejected_audit():
    result = EmpireOrchestrator(EmpireCapabilityExecutor()).execute_plan(plan("unknown_command"))

    assert result["status"] == OrchestrationStatus.REJECTED.value
    assert result["audit"][0]["status"] == "rejected"
    assert result["audit"][0]["verified"] is False


def test_malformed_capability_result_creates_failed_audit(tmp_path: Path):
    class MalformedExecutor(EmpireCapabilityExecutor):
        def execute(self, capability, task):
            return "malformed"

    result = EmpireOrchestrator(MalformedExecutor(project_root=tmp_path)).execute_plan(plan())

    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["audit"][0]["status"] == "failed"
    assert result["audit"][0]["verified"] is False


def test_permission_rejection_is_audited():
    execution_plan = plan()
    execution_plan["tasks"][0]["requires_permission"] = True

    result = EmpireOrchestrator(EmpireCapabilityExecutor()).execute_plan(execution_plan, approved=False)

    assert result["status"] == OrchestrationStatus.REJECTED.value
    assert result["audit"][0]["status"] == "rejected"
    assert result["audit"][0]["error"] == "Permission not approved."
