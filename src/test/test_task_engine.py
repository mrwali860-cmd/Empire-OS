import pytest

from src.agent.task_engine import TaskEngine
from src.agent.tasks import Task, TaskStatus


def make_task(task_id="task-1"):
    return Task(
        id=task_id,
        name="Test task",
        description="Run a test task.",
        command="run_tests",
    )


def test_add_task_requires_task_instance():
    engine = TaskEngine()

    with pytest.raises(TypeError, match="Task must be a Task instance"):
        engine.add_task(object())


def test_add_task_rejects_empty_id():
    engine = TaskEngine()
    task = make_task()
    task.id = "   "

    with pytest.raises(ValueError, match="Task ID must be a non-empty string"):
        engine.add_task(task)


def test_add_task_rejects_duplicate_id():
    engine = TaskEngine()
    engine.add_task(make_task())

    with pytest.raises(ValueError, match="Task already exists"):
        engine.add_task(make_task())


def test_valid_completion_lifecycle():
    engine = TaskEngine()
    task = engine.add_task(make_task())

    assert task.status is TaskStatus.PENDING
    assert engine.start_task(task.id).status is TaskStatus.RUNNING
    assert engine.complete_task(task.id, {"ok": True}).status is TaskStatus.COMPLETED
    assert task.result == {"ok": True}


def test_valid_failure_lifecycle():
    engine = TaskEngine()
    task = engine.add_task(make_task())

    engine.start_task(task.id)
    failed = engine.fail_task(task.id, "test failure")

    assert failed.status is TaskStatus.FAILED
    assert failed.error == "test failure"


def test_invalid_lifecycle_transitions_are_rejected():
    engine = TaskEngine()
    task = engine.add_task(make_task())

    with pytest.raises(ValueError, match="cannot complete"):
        engine.complete_task(task.id)

    with pytest.raises(ValueError, match="cannot fail"):
        engine.fail_task(task.id, "not running")

    engine.start_task(task.id)

    with pytest.raises(ValueError, match="cannot start"):
        engine.start_task(task.id)

    engine.complete_task(task.id)

    with pytest.raises(ValueError, match="cannot start"):
        engine.start_task(task.id)

    with pytest.raises(ValueError, match="cannot complete"):
        engine.complete_task(task.id)

    with pytest.raises(ValueError, match="cannot fail"):
        engine.fail_task(task.id, "already complete")


def test_running_task_cannot_be_removed():
    engine = TaskEngine()
    task = engine.add_task(make_task())
    engine.start_task(task.id)

    with pytest.raises(ValueError, match="Running tasks cannot be removed"):
        engine.remove_task(task.id)


def test_missing_task_raises_key_error():
    engine = TaskEngine()

    with pytest.raises(KeyError, match="Task not found"):
        engine.start_task("missing")


def test_to_dict_serialization_contract():
    engine = TaskEngine()
    task = engine.add_task(make_task())

    serialized = engine.to_dict()

    assert isinstance(serialized, list)
    assert len(serialized) == 1

    item = serialized[0]
    required_keys = {
        "id",
        "name",
        "description",
        "command",
        "requires_permission",
        "status",
        "result",
        "error",
        "created_at",
        "started_at",
        "completed_at",
    }

    assert required_keys.issubset(item)
    assert item["id"] == task.id
    assert item["status"] == TaskStatus.PENDING.value
    assert isinstance(item["created_at"], str)
    assert item["started_at"] is None
    assert item["completed_at"] is None


def test_summary_counts_all_lifecycle_states():
    engine = TaskEngine()
    first = engine.add_task(make_task("task-1"))
    second = engine.add_task(make_task("task-2"))
    third = engine.add_task(make_task("task-3"))

    engine.start_task(first.id)
    engine.complete_task(first.id)
    engine.start_task(second.id)
    engine.fail_task(second.id, "failed")
    third.reject("rejected")

    summary = engine.summary()

    assert summary == {
        TaskStatus.PENDING.value: 0,
        TaskStatus.RUNNING.value: 0,
        TaskStatus.COMPLETED.value: 1,
        TaskStatus.FAILED.value: 1,
        TaskStatus.REJECTED.value: 1,
    }

# CI trigger marker: no functional behavior change.
