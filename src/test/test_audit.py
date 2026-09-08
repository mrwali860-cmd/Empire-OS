import pytest

from src.agent.audit import AuditRecord, ExecutionAudit


def test_audit_record_serializes():
    record = AuditRecord(
        task_id="TASK-001",
        command="run_tests",
        capability="test_runner",
        status="completed",
        verified=True,
        result={"return_code": 0},
    )

    assert record.to_dict() == {
        "task_id": "TASK-001",
        "command": "run_tests",
        "capability": "test_runner",
        "status": "completed",
        "verified": True,
        "error": None,
        "result": {"return_code": 0},
    }


def test_audit_records_preserve_execution_order():
    audit = ExecutionAudit()
    audit.record(AuditRecord("TASK-001", "inspect_project", "project_inspection", "completed", True))
    audit.record(AuditRecord("TASK-002", "run_tests", "test_runner", "completed", True))

    assert [record.task_id for record in audit.records] == ["TASK-001", "TASK-002"]


def test_audit_records_failed_execution():
    audit = ExecutionAudit()
    audit.record(AuditRecord("TASK-001", "run_tests", "test_runner", "failed", False, "Tests failed."))

    record = audit.records[0]
    assert record.status == "failed"
    assert record.verified is False
    assert record.error == "Tests failed."


def test_audit_records_rejected_execution():
    audit = ExecutionAudit()
    audit.record(AuditRecord("TASK-001", "unknown", "", "rejected", False, "No capability registered."))

    record = audit.records[0]
    assert record.status == "rejected"
    assert record.verified is False


def test_audit_is_immutable_snapshot():
    audit = ExecutionAudit()
    audit.record(AuditRecord("TASK-001", "inspect_project", "project_inspection", "completed", True))

    snapshot = audit.records
    audit.record(AuditRecord("TASK-002", "run_tests", "test_runner", "failed", False))

    assert len(snapshot) == 1
    assert len(audit.records) == 2


def test_audit_clear_removes_current_execution_records():
    audit = ExecutionAudit()
    audit.record(AuditRecord("TASK-001", "inspect_project", "project_inspection", "completed", True))

    audit.clear()

    assert audit.records == ()
    assert audit.as_dicts() == []


def test_audit_record_rejects_invalid_identity_fields():
    with pytest.raises(TypeError, match="task_id must be a string"):
        AuditRecord(123, "cmd", "cap", "completed", True)
    with pytest.raises(ValueError, match="command must be non-empty"):
        AuditRecord("task-1", "  ", "cap", "completed", True)
    with pytest.raises(ValueError, match="capability must be non-empty"):
        AuditRecord("task-1", "cmd", "  ", "completed", True)


def test_audit_record_rejects_invalid_status_and_verified_flag():
    with pytest.raises(ValueError, match="status is invalid"):
        AuditRecord("task-1", "cmd", "cap", "unknown", True)
    with pytest.raises(TypeError, match="verified must be a bool"):
        AuditRecord("task-1", "cmd", "cap", "completed", 1)


def test_audit_record_enforces_bounded_safe_result():
    with pytest.raises(TypeError, match="result must be a dictionary"):
        AuditRecord("task-1", "cmd", "cap", "completed", True, result=[])
    with pytest.raises(ValueError, match="result is too large"):
        AuditRecord("task-1", "cmd", "cap", "completed", True, result={"output": "x" * 4001})
    with pytest.raises(ValueError, match="result contains unsafe key"):
        AuditRecord("task-1", "cmd", "cap", "completed", True, result={"api_key": "secret"})


def test_audit_record_is_immutable_and_serializable():
    record = AuditRecord("task-1", "cmd", "cap", "completed", True, result={"ok": True})
    assert record.to_dict()["result"] == {"ok": True}
    with pytest.raises((AttributeError, TypeError)):
        record.status = "failed"
