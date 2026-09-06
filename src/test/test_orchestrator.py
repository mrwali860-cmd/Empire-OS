from src.agent.capabilities import EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus
from src.agent.tasks import Task, TaskStatus


def make_task(command="run_tests", requires_permission=False):
    return Task(id="TASK-001", name="Run tests", description="Run the test suite", command=command, requires_permission=requires_permission)


def test_orchestrator_routes_supported_task():
    orchestrator = EmpireOrchestrator()
    decision = orchestrator.route(make_task())
    assert decision.accepted is True
    assert decision.capability == "test_runner"


def test_orchestrator_routes_file_write_capability():
    orchestrator = EmpireOrchestrator()
    decision = orchestrator.route(make_task(command="file_write"))
    assert decision.accepted is True
    assert decision.capability == "file_write"


def test_orchestrator_rejects_unknown_task():
    orchestrator = EmpireOrchestrator()
    decision = orchestrator.route(make_task(command="unknown"))
    assert decision.accepted is False
    assert "No capability" in decision.reason


def test_orchestrator_rejects_unregistered_capability():
    orchestrator = EmpireOrchestrator(EmpireCapabilityExecutor())
    orchestrator.routes["run_tests"] = "missing_capability"
    decision = orchestrator.route(make_task())
    assert decision.accepted is False
    assert decision.capability == "missing_capability"
    assert "not registered" in decision.reason


def ready_plan(**overrides):
    plan = {
        "status": "READY",
        "plan_id": "PLAN-001",
        "goal": "Run the test suite",
        "tasks": [{
            "id": "TASK-001",
            "title": "Run tests",
            "description": "Run the test suite",
            "action": "run_tests",
            "requires_permission": False,
        }],
    }
    plan.update(overrides)
    return plan


def test_orchestrator_executes_plan_in_order():
    calls = []
    plan = ready_plan(tasks=[
        {"id": "TASK-001", "title": "Run tests", "description": "Run tests", "action": "run_tests", "requires_permission": False},
        {"id": "TASK-002", "title": "Run tests again", "description": "Run tests again", "action": "run_tests", "requires_permission": False},
    ])
    result = EmpireOrchestrator().execute_plan(plan, executor=lambda task: calls.append(task.id) or {"ok": True})
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["goal"] == "Run the test suite"
    assert result["completed_tasks"] == 2
    assert calls == ["TASK-001", "TASK-002"]


def test_orchestrator_returns_completed_task_results():
    result = EmpireOrchestrator().execute_plan(ready_plan(), executor=lambda task: {"ok": True, "summary": "passed"})
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["task_results"][0]["status"] == TaskStatus.COMPLETED.value
    assert result["task_results"][0]["result"] == {"ok": True, "summary": "passed"}
    assert result["current_task"] is None


def test_orchestrator_stops_when_permission_is_missing():
    plan = ready_plan(tasks=[{
        "id": "TASK-001", "title": "Inspect project", "description": "Inspect the project",
        "action": "inspect_project", "requires_permission": True,
    }])
    result = EmpireOrchestrator().execute_plan(plan, executor=lambda task: {"ok": True}, approved=False)
    assert result["status"] == OrchestrationStatus.REJECTED.value
    assert result["completed_tasks"] == 0
    assert result["failed_task_id"] == "TASK-001"
    assert result["task_results"][0]["status"] == TaskStatus.REJECTED.value
    assert result["audit"][0]["status"] == "rejected"


def test_orchestrator_stops_on_unknown_task_and_audits_rejection():
    plan = ready_plan(tasks=[{"id": "TASK-UNKNOWN", "title": "Unknown", "description": "Unknown command", "action": "unknown", "requires_permission": False}])
    result = EmpireOrchestrator().execute_plan(plan)
    assert result["status"] == OrchestrationStatus.REJECTED.value
    assert result["failed_task_id"] == "TASK-UNKNOWN"
    assert result["audit"][0]["status"] == "rejected"
    assert "No capability" in result["audit"][0]["error"]


def test_orchestrator_stops_on_failed_verification():
    plan = ready_plan(tasks=[
        {"id": "TASK-001", "title": "Run tests", "description": "Run tests", "action": "run_tests", "requires_permission": False},
        {"id": "TASK-002", "title": "Should not run", "description": "This must not execute", "action": "run_tests", "requires_permission": False},
    ])
    calls = []
    result = EmpireOrchestrator().execute_plan(plan, executor=lambda task: calls.append(task.id) or {"ok": False}, verifier=lambda task, output: bool(output.get("ok")))
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["completed_tasks"] == 0
    assert result["failed_task_id"] == "TASK-001"
    assert result["task_results"][0]["status"] == TaskStatus.FAILED.value
    assert result["task_results"][1]["status"] == TaskStatus.PENDING.value
    assert calls == ["TASK-001"]


def test_orchestrator_rejects_plan_without_plan_id():
    result = EmpireOrchestrator().execute_plan(ready_plan(plan_id=""))
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["error"] == "Plan must include a non-empty plan_id."


def test_orchestrator_rejects_plan_without_tasks():
    result = EmpireOrchestrator().execute_plan(ready_plan(tasks=[]))
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["error"] == "Plan must include at least one task."


def test_orchestrator_rejects_task_without_required_fields():
    result = EmpireOrchestrator().execute_plan(ready_plan(tasks=[{"id": "TASK-001"}]))
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["error"] == "Task 1 is missing required field(s): action."


def test_orchestrator_rejects_duplicate_task_ids_before_execution():
    calls = []
    duplicate = {"id": "TASK-001", "title": "Second", "description": "Duplicate", "action": "run_tests", "requires_permission": False}
    result = EmpireOrchestrator().execute_plan(ready_plan(tasks=[
        {"id": "TASK-001", "title": "First", "description": "First", "action": "run_tests", "requires_permission": False},
        duplicate,
    ]), executor=lambda task: calls.append(task.id) or {"ok": True})
    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["error"] == "Duplicate task id: TASK-001"
    assert calls == []
