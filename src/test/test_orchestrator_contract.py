import pytest

from src.agent.orchestrator import EmpireOrchestrator


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


def test_plan_must_be_dict():
    result = EmpireOrchestrator().execute_plan(None)
    assert result["error"] == "Plan must be a dictionary."


def test_plan_id_and_goal_types_are_validated():
    orchestrator = EmpireOrchestrator()
    assert orchestrator.execute_plan(ready_plan(plan_id=123))["error"] == "Plan must include a non-empty plan_id."
    assert orchestrator.execute_plan(ready_plan(goal=123))["error"] == "Plan goal must be a string."


def test_plan_and_task_limits_are_enforced():
    orchestrator = EmpireOrchestrator()
    assert orchestrator.execute_plan(ready_plan(plan_id="x" * 201))["error"] == "Plan ID exceeds 200 characters."
    assert orchestrator.execute_plan(ready_plan(goal="x" * 2001))["error"] == "Plan goal exceeds 2000 characters."
    tasks = [dict(ready_plan()["tasks"][0], id=f"TASK-{i}") for i in range(101)]
    assert orchestrator.execute_plan(ready_plan(tasks=tasks))["error"] == "Plan cannot contain more than 100 tasks."


def test_task_field_types_and_bounds_are_validated():
    orchestrator = EmpireOrchestrator()
    assert orchestrator.execute_plan(ready_plan(tasks=[{"id": "TASK-1", "action": "run_tests", "title": 1}]))["error"] == "Task 1 title must be a string."
    assert orchestrator.execute_plan(ready_plan(tasks=[{"id": "TASK-1", "action": "run_tests", "description": 1}]))["error"] == "Task 1 description must be a string."
    assert orchestrator.execute_plan(ready_plan(tasks=[{"id": "TASK-1", "action": "run_tests", "requires_permission": 1}]))["error"] == "Task 1 requires_permission must be a boolean."
    assert orchestrator.execute_plan(ready_plan(tasks=[{"id": "TASK-1", "action": "run_tests", "title": "x" * 2001}]))["error"] == "Task 1 title exceeds 2000 characters."
    assert orchestrator.execute_plan(ready_plan(tasks=[{"id": "TASK-1", "action": "run_tests", "description": "x" * 2001}]))["error"] == "Task 1 description exceeds 2000 characters."


def test_executor_verifier_and_approval_types_are_validated():
    orchestrator = EmpireOrchestrator()
    assert orchestrator.execute_plan(ready_plan(), executor=1)["error"] == "Executor must be callable."
    assert orchestrator.execute_plan(ready_plan(), verifier=1)["error"] == "Verifier must be callable."
    assert orchestrator.execute_plan(ready_plan(), approved=1)["error"] == "approved must be a boolean."


def test_task_identity_is_not_coerced():
    orchestrator = EmpireOrchestrator()
    result = orchestrator.execute_plan(ready_plan(tasks=[{"id": 123, "action": "run_tests"}]))
    assert result["error"] == "Task 1 must include a non-empty string id."


def test_action_identity_is_not_coerced():
    orchestrator = EmpireOrchestrator()
    result = orchestrator.execute_plan(ready_plan(tasks=[{"id": "TASK-1", "action": 123}]))
    assert result["error"] == "Task 1 must include a non-empty string action."


def test_classify_rejects_non_task():
    with pytest.raises(TypeError, match="Task must be a Task instance"):
        EmpireOrchestrator().classify(None)
