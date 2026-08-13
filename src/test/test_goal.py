"""
Tests for Empire OS Goal Engine.
"""

import pytest

from src.agent.goal import GoalEngine
from src.agent.task_engine import TaskEngine


def make_engine() -> GoalEngine:
    return GoalEngine(TaskEngine())


def test_create_goal():
    engine = make_engine()

    goal = engine.create_goal(
        title="Improve Empire OS",
        description="Build the goal execution pipeline.",
    )

    assert goal.id.startswith("goal-")
    assert goal.title == "Improve Empire OS"
    assert goal.description == (
        "Build the goal execution pipeline."
    )


def test_create_goal_rejects_empty_title():
    engine = make_engine()

    with pytest.raises(ValueError):
        engine.create_goal(
            title="",
            description="Build the system.",
        )


def test_create_goal_rejects_empty_description():
    engine = make_engine()

    with pytest.raises(ValueError):
        engine.create_goal(
            title="Build Empire OS",
            description="",
        )


def test_get_goal():
    engine = make_engine()

    goal = engine.create_goal(
        title="Build Empire OS",
        description="Create the execution system.",
    )

    found = engine.get_goal(goal.id)

    assert found == goal


def test_plan_goal_creates_expected_tasks():
    engine = make_engine()

    goal = engine.create_goal(
        title="Build Empire OS",
        description="Create the execution system.",
    )

    tasks = engine.plan_goal(goal)

    assert len(tasks) == 2

    assert tasks[0].command == "inspect_project"
    assert tasks[0].requires_permission is True

    assert tasks[1].command == "run_tests"
    assert tasks[1].requires_permission is False


def test_queue_goal_adds_tasks_to_task_engine():
    task_engine = TaskEngine()
    engine = GoalEngine(task_engine)

    goal = engine.create_goal(
        title="Build Empire OS",
        description="Create the execution system.",
    )

    tasks = engine.queue_goal(goal)

    assert len(tasks) == 2
    assert len(task_engine.list_tasks()) == 2

    summary = task_engine.summary()

    assert summary["pending"] == 2
    assert summary["running"] == 0
    assert summary["completed"] == 0
    assert summary["failed"] == 0


def test_create_and_queue():
    task_engine = TaskEngine()
    engine = GoalEngine(task_engine)

    goal, tasks = engine.create_and_queue(
        title="Run Empire OS",
        description="Execute the current system workflow.",
    )

    assert goal.title == "Run Empire OS"
    assert len(tasks) == 2
    assert len(task_engine.list_tasks()) == 2