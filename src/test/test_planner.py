"""Tests for the structured execution planning contract."""

from src.brain.planner import ExecutionPlanner


def test_approved_decision_creates_structured_tasks():
    planner = ExecutionPlanner()
    decision = {"status": "APPROVED", "decision": "Goal: Build the system\nNext actions:\n1. Inspect the project\n2. Run tests\n3. Define the next milestone"}
    plan = planner.plan(decision)
    assert plan["status"] == "READY"
    assert plan["plan_id"].startswith("PLAN-")
    assert plan["verification_required"] is True
    assert len(plan["tasks"]) == 3
    assert plan["tasks"][0]["action"] == "inspect_project"
    assert plan["tasks"][1]["action"] == "run_tests"
    assert plan["tasks"][2]["action"] == "MANUAL_REVIEW"
    assert plan["tasks"][2]["requires_permission"] is True
    assert plan["tasks"][0]["status"] == "PENDING"


def test_git_status_action_maps_to_capability():
    plan = ExecutionPlanner().plan({"status": "APPROVED", "decision": "Goal: Check repository status\n1. Check Git status"})
    assert plan["tasks"][0]["action"] == "git_status"
    assert plan["tasks"][0]["requires_permission"] is False


def test_repository_status_action_maps_to_capability():
    plan = ExecutionPlanner().plan({"status": "APPROVED", "decision": "Goal: Check repository status\n1. Check repository status"})
    assert plan["tasks"][0]["action"] == "git_status"


def test_project_search_action_maps_to_capability():
    plan = ExecutionPlanner().plan({"status": "APPROVED", "decision": "Goal: Find requested code\n1. Search project source files"})
    assert plan["tasks"][0]["action"] == "project_search"
    assert plan["tasks"][0]["requires_permission"] is False


def test_file_write_requires_permission():
    plan = ExecutionPlanner().plan({"status": "APPROVED", "decision": "Goal: Update project file\n1. Write file: app.py content: VALUE = 42"})
    assert plan["tasks"][0]["action"] == "file_write"
    assert plan["tasks"][0]["requires_permission"] is True


def test_rejected_decision_has_no_tasks():
    plan = ExecutionPlanner().plan({"status": "FAILED", "decision": "Do not execute"})
    assert plan["status"] == "FAILED"
    assert plan["plan_id"] is None
    assert plan["tasks"] == []
    assert plan["verification_required"] is True


def test_arbitrary_text_never_becomes_shell_execution():
    plan = ExecutionPlanner().plan({"status": "APPROVED", "decision": "1. Run an arbitrary command on the machine"})
    task = plan["tasks"][0]
    assert task["action"] == "MANUAL_REVIEW"
    assert task["requires_permission"] is True
