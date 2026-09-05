from pathlib import Path

import pytest

from src.agent.capabilities import CapabilityError, CapabilityRegistry, CapabilityResult, EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus
from src.agent.tasks import Task


def make_task(command="inspect_project", description="Test capability execution"):
    return Task(id="TASK-001", name="Capability test", description=description, command=command, requires_permission=False)


def make_plan(action="inspect_project", description="Test"):
    return {"status": "READY", "plan_id": "PLAN-CAP-001", "goal": "Capability verification", "tasks": [{"id": "TASK-001", "title": "Capability", "description": description, "action": action, "requires_permission": False}]}


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
    assert executor.registry.names == ("file_read", "git_status", "project_inspection", "project_search", "test_runner")
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


def test_project_search_finds_matching_lines(tmp_path: Path):
    source = tmp_path / "app.py"
    source.write_text("def hello():\n    return 'hello world'\n", encoding="utf-8")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute("project_search", make_task("project_search", "Execute planned step: hello"))
    assert result.ok is True
    assert result.data["query"] == "hello"
    assert result.data["matches"] == [
        {"file": "app.py", "line": 1, "text": "def hello():"},
        {"file": "app.py", "line": 2, "text": "    return 'hello world'"},
    ]
    assert result.data["truncated"] is False


def test_project_search_completed_and_audited(tmp_path: Path):
    (tmp_path / "app.py").write_text("CapabilityResult\n", encoding="utf-8")
    result = EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)).execute_plan(
        make_plan("project_search", "Execute planned step: CapabilityResult")
    )
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1
    audit = result["audit"][0]
    assert audit["capability"] == "project_search"
    assert audit["verified"] is True
    assert audit["result"]["data"]["matches"][0]["file"] == "app.py"


def test_project_search_malformed_result_failed(tmp_path: Path):
    class MalformedExecutor(EmpireCapabilityExecutor):
        def execute(self, capability, task):
            if capability == "project_search":
                return CapabilityResult(True, "project_search", {"matches": "invalid"})
            return super().execute(capability, task)

    result = EmpireOrchestrator(MalformedExecutor()).execute_plan(
        make_plan("project_search", "Execute planned step: hello")
    )
    assert result["status"] == OrchestrationStatus.FAILED.value


def test_file_read_is_bounded_and_verified(tmp_path: Path):
    (tmp_path / "app.py").write_text("VALUE = 42\n", encoding="utf-8")
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = executor.execute("file_read", make_task("file_read", "Execute planned step: read file app.py"))
    assert result.ok is True
    assert result.data["path"] == "app.py"
    assert result.data["content"] == "VALUE = 42\n"
    assert executor.verify("file_read", result) is True


def test_file_read_completed_and_audited(tmp_path: Path):
    (tmp_path / "app.py").write_text("VALUE = 42\n", encoding="utf-8")
    result = EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)).execute_plan(
        make_plan("file_read", "Execute planned step: read file app.py")
    )
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    assert result["completed_tasks"] == 1
    audit = result["audit"][0]
    assert audit["capability"] == "file_read"
    assert audit["verified"] is True
    assert audit["result"]["data"]["content"] == "VALUE = 42\n"


def test_file_read_path_traversal_rejected(tmp_path: Path):
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_read", make_task("file_read", "Execute planned step: read file ../secret.txt")
    )
    assert result.ok is False
    assert EmpireCapabilityExecutor(project_root=tmp_path).verify("file_read", result) is False


def test_file_read_malformed_result_failed(tmp_path: Path):
    class MalformedExecutor(EmpireCapabilityExecutor):
        def execute(self, capability, task):
            if capability == "file_read":
                return CapabilityResult(True, "file_read", {"path": "app.py"})
            return super().execute(capability, task)

    result = EmpireOrchestrator(MalformedExecutor()).execute_plan(
        make_plan("file_read", "Execute planned step: read file app.py")
    )
    assert result["status"] == OrchestrationStatus.FAILED.value


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


def _mock_git(monkeypatch, branch="main", commit_sha="a" * 40, porcelain=""):
    outputs = {
        ("rev-parse", "--abbrev-ref", "HEAD"): branch + "\n",
        ("rev-parse", "HEAD"): commit_sha + "\n",
        ("status", "--porcelain"): porcelain,
    }

    class Completed:
        def __init__(self, stdout):
            self.stdout = stdout

    def fake_run(command, **kwargs):
        return Completed(outputs[tuple(command[1:])])

    monkeypatch.setattr("src.agent.git_status.subprocess.run", fake_run)


def test_git_status_clean_repository_evidence(monkeypatch, tmp_path: Path):
    _mock_git(monkeypatch, porcelain="")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute("git_status", make_task("git_status"))
    assert result.ok is True
    assert result.data["branch"] == "main"
    assert result.data["clean"] is True
    assert result.data["changed_files"] == []
    assert len(result.data["commit_sha"]) == 40


def test_git_status_dirty_repository_evidence(monkeypatch, tmp_path: Path):
    _mock_git(monkeypatch, porcelain=" M src/app.py\n?? notes.txt\n")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute("git_status", make_task("git_status"))
    assert result.ok is True
    assert result.data["clean"] is False
    assert result.data["changed_files"] == ["src/app.py", "notes.txt"]
    assert EmpireCapabilityExecutor(project_root=tmp_path).verify("git_status", result) is True


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
