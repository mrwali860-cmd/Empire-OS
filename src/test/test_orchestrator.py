from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus
from src.agent.tasks import Task


def make_task(command="run_tests", requires_permission=False):
    return Task(
        id="TASK-001",
        name="Run tests",
        description="Run the test suite",
        command=command,
        requires_permission=requires_permission,
    )


def test_orchestrator_routes_supported_task():
    orchestrator = EmpireOrchestrator()

    decision = orchestrator.route(make_task())

    assert decision.accepted is True
    assert decision.capability == "test_runner"


def test_orchestrator_rejects_unknown_task():
    orchestrator = EmpireOrchestrator()

    decision = orchestrator.route(make_task(command="unknown"))

    assert decision.accepted is False
    assert "No capability" in decision.reason


def test_orchestrator_executes_plan_in_order():
    calls = []

    def executor(task):
        calls.append(task.id)
        return {"ok": True}

    plan = {
        "status": "READY",
        "plan_id": "PLAN-001",
        "goal": "Run the test suite",
        "tasks": [
            {
                "id": "TASK-001",
                "title": "Run tests",
                "description": "Run the test suite",
                "action": "run_tests",
                "requires_permission": False,
                "verification": "Tests pass.",
                "status": "PENDING",
            },
            {
                "id": "TASK-002",
                "title": "Run tests again",
                "description": "Run the test suite again",
                "action": "run_tests",
                "requires_permission": False,
                "verification": "Tests pass.",
                "status": "PENDING",
            },
        ],
    }

    result = EmpireOrchestrator().execute_plan(plan, executor=executor)

    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["goal"] == "Run the test suite"
    assert result["completed_tasks"] == 2
    assert calls == ["TASK-001", "TASK-002"]


def test_orchestrator_stops_when_permission_is_missing():
    plan = {
        "status": "READY",
        "plan_id": "PLAN-002",
        "goal": "Inspect project",
        "tasks": [
            {
                "id": "TASK-001",
                "title": "Inspect project",
                "description": "Inspect the project",
                "action": "inspect_project",
                "requires_permission": True,
                "verification": "Inspection succeeds.",
                "status": "PENDING",
            }
        ],
    }

    result = EmpireOrchestrator().execute_plan(
        plan,
        executor=lambda task: {"ok": True},
        approved=False,
    )

    assert result["status"] == OrchestrationStatus.REJECTED.value
    assert result["completed_tasks"] == 0
    assert result["failed_task_id"] == "TASK-001"


def test_orchestrator_stops_on_failed_verification():
    def executor(task):
        return {"ok": False}

    def verifier(task, result):
        return bool(result.get("ok"))

    plan = {
        "status": "READY",
        "plan_id": "PLAN-003",
        "goal": "Verify work",
        "tasks": [
            {
                "id": "TASK-001",
                "title": "Run tests",
                "description": "Run tests",
                "action": "run_tests",
                "requires_permission": False,
                "verification": "Tests pass.",
                "status": "PENDING",
            },
            {
                "id": "TASK-002",
                "title": "Should not run",
                "description": "This must not execute",
                "action": "run_tests",
                "requires_permission": False,
                "verification": "Never reached.",
                "status": "PENDING",
            },
        ],
    }

    calls = []

    def tracked_executor(task):
        calls.append(task.id)
        return executor(task)

    result = EmpireOrchestrator().execute_plan(
        plan,
        executor=tracked_executor,
        verifier=verifier,
    )

    assert result["status"] == OrchestrationStatus.FAILED.value
    assert result["completed_tasks"] == 0
    assert result["failed_task_id"] == "TASK-001"
    assert calls == ["TASK-001"]
