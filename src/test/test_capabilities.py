

def test_registry_contract_rejects_result_capability_mismatch():
    registry = CapabilityRegistry()
    registry.register("demo", lambda task: CapabilityResult(True, "other"))
    with pytest.raises(CapabilityError, match="result mismatch"):
        registry.execute("demo", make_task())


def test_default_executor_registers_real_routes(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    assert executor.registry.names == ("decision_engine", "file_read", "file_write", "git_status", "project_inspection", "project_search", "test_runner")
    result = executor.execute("project_inspection", make_task())
    assert isinstance(result, CapabilityResult)
    assert result.ok is True
    assert result.capability == "project_inspection"


def test_file_write_requires_orchestrator_permission(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = EmpireOrchestrator(executor).execute_plan(make_plan("file_write", "Execute planned step: write file: app.py content: VALUE = 42\n", True), approved=False)
