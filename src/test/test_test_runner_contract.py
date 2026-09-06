from src.agent.capabilities import CapabilityResult, EmpireCapabilityExecutor


def make_result(data, *, ok=True, error=None):
    return CapabilityResult(ok=ok, capability="test_runner", data=data, error=error)


def valid_data():
    return {"return_code": 0, "stdout": "1 passed", "stderr": ""}


def test_test_runner_valid_success_contract_passes(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    assert executor.verify("test_runner", make_result(valid_data())) is True


def test_test_runner_missing_return_code_fails(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    data = valid_data()
    del data["return_code"]
    assert executor.verify("test_runner", make_result(data)) is False


def test_test_runner_boolean_return_code_fails(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    data = valid_data()
    data["return_code"] = False
    assert executor.verify("test_runner", make_result(data)) is False


def test_test_runner_nonzero_return_code_fails(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    data = valid_data()
    data["return_code"] = 1
    assert executor.verify("test_runner", make_result(data, ok=False, error="Test suite failed with exit code 1.")) is False


def test_test_runner_stdout_must_be_string(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    data = valid_data()
    data["stdout"] = ["1 passed"]
    assert executor.verify("test_runner", make_result(data)) is False


def test_test_runner_stderr_must_be_string(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    data = valid_data()
    data["stderr"] = {"message": ""}
    assert executor.verify("test_runner", make_result(data)) is False


def test_test_runner_stdout_max_length_is_enforced(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    data = valid_data()
    data["stdout"] = "x" * 4001
    assert executor.verify("test_runner", make_result(data)) is False


def test_test_runner_stderr_max_length_is_enforced(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    data = valid_data()
    data["stderr"] = "x" * 4001
    assert executor.verify("test_runner", make_result(data)) is False


def test_test_runner_failed_result_never_verifies(tmp_path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    assert executor.verify(
        "test_runner",
        make_result(valid_data(), ok=False, error="Test suite failed with exit code 1."),
    ) is False
