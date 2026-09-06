from pathlib import Path

from src.agent.capabilities import CapabilityResult, EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator, OrchestrationStatus
from src.agent.tasks import Task
from src.agent.file_write import FileWriteCapability


def make_task(description: str, permission: bool = False) -> Task:
    return Task(
        id="TASK-FW-CONTRACT-001",
        name="File write contract",
        description=description,
        command="file_write",
        requires_permission=permission,
    )


def make_plan(description: str, permission: bool = True) -> dict:
    return {
        "status": "READY",
        "plan_id": "PLAN-FW-CONTRACT-001",
        "goal": "Verify file write contract",
        "tasks": [{
            "id": "TASK-FW-CONTRACT-001",
            "title": "File write",
            "description": description,
            "action": "file_write",
            "requires_permission": permission,
        }],
    }


def test_file_write_input_contract_rejects_missing_path(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = executor.execute("file_write", make_task("Execute planned step: write file: content: hello"))
    assert result.ok is False
    assert result.error == "File path is required."


def test_file_write_input_validator_is_registered(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    contract = executor.registry.get("file_write")
    assert contract.validate_input(make_task("Execute planned step: write file: app.py content: hello")) is True
    assert contract.validate_input(make_task("Execute planned step: write file: content: hello")) is False


def test_file_write_requires_permission_before_mutation(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = EmpireOrchestrator(executor).execute_plan(
        make_plan("Execute planned step: write file: app.py content: blocked\n", True),
        approved=False,
    )
    assert result["status"] == OrchestrationStatus.REJECTED.value
    assert not (tmp_path / "app.py").exists()
    assert result["audit"][0]["status"] == "rejected"


def test_file_write_success_has_verifiable_evidence_and_audit(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = EmpireOrchestrator(executor).execute_plan(
        make_plan("Execute planned step: write file: app.py content: VALUE = 42\n", True),
        approved=True,
    )
    assert result["status"] == OrchestrationStatus.COMPLETED.value
    evidence = result["capability_results"][0]
    assert evidence["capability"] == "file_write"
    assert evidence["data"]["path"] == "app.py"
    assert evidence["data"]["bytes_written"] == len("VALUE = 42\n".encode())
    assert len(evidence["data"]["sha256"]) == 64
    assert result["audit"][0]["verified"] is True
    assert result["audit"][0]["result"] == evidence
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "VALUE = 42\n"


def test_file_write_verifier_checks_actual_file_bytes(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = executor.execute("file_write", make_task("Execute planned step: write file: app.py content: hello"))
    assert executor.verify("file_write", result) is True
    (tmp_path / "app.py").write_text("tampered", encoding="utf-8")
    assert executor.verify("file_write", result) is False


def test_file_write_verifier_rejects_malformed_evidence(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    malformed = CapabilityResult(
        True,
        "file_write",
        {"path": "app.py", "bytes_written": 4, "sha256": "0" * 64},
    )
    assert executor.verify("file_write", malformed) is False


def test_file_write_rejects_path_traversal_without_mutation(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    outside = tmp_path.parent / "secret.txt"
    result = executor.execute(
        "file_write", make_task("Execute planned step: write file: ../secret.txt content: blocked")
    )
    assert result.ok is False
    assert not outside.exists()


def test_file_write_enforces_byte_limit(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    oversized = "x" * (FileWriteCapability.MAX_BYTES + 1)
    result = executor.execute(
        "file_write", make_task(f"Execute planned step: write file: large.txt content: {oversized}")
    )
    assert result.ok is False
    assert "size limit" in result.error
    assert not (tmp_path / "large.txt").exists()


def test_file_write_preserves_unicode_utf8_and_reports_bytes(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    content = "سلام Empire OS 🚀\n"
    result = executor.execute(
        "file_write", make_task(f"Execute planned step: write file: unicode.txt content: {content}")
    )
    assert result.ok is True
    assert (tmp_path / "unicode.txt").read_text(encoding="utf-8") == content
    assert result.data["bytes_written"] == len(content.encode("utf-8"))
    assert executor.verify("file_write", result) is True
