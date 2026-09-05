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
