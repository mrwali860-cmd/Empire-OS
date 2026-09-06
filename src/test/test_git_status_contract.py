from src.agent.capabilities import CapabilityResult, EmpireCapabilityExecutor


def _valid_result(**overrides):
    data = {
        "branch": "main",
        "clean": True,
        "changed_files": [],
        "commit_sha": "a" * 40,
    }
    data.update(overrides)
    return CapabilityResult(ok=True, capability="git_status", data=data, error=None)


def test_git_status_valid_contract():
    executor = EmpireCapabilityExecutor()
    assert executor.verify("git_status", _valid_result()) is True


def test_git_status_rejects_missing_branch():
    result = _valid_result()
    del result.data["branch"]
    assert EmpireCapabilityExecutor().verify("git_status", result) is False


def test_git_status_rejects_empty_branch():
    assert EmpireCapabilityExecutor().verify("git_status", _valid_result(branch="")) is False


def test_git_status_rejects_non_boolean_clean():
    assert EmpireCapabilityExecutor().verify("git_status", _valid_result(clean=1)) is False


def test_git_status_rejects_non_list_changed_files():
    assert EmpireCapabilityExecutor().verify("git_status", _valid_result(changed_files="file.py")) is False


def test_git_status_rejects_non_string_changed_file():
    assert EmpireCapabilityExecutor().verify("git_status", _valid_result(changed_files=[1])) is False


def test_git_status_rejects_missing_commit_sha():
    result = _valid_result()
    del result.data["commit_sha"]
    assert EmpireCapabilityExecutor().verify("git_status", result) is False


def test_git_status_rejects_malformed_commit_sha():
    executor = EmpireCapabilityExecutor()
    assert executor.verify("git_status", _valid_result(commit_sha="a" * 39)) is False
    assert executor.verify("git_status", _valid_result(commit_sha="g" * 40)) is False


def test_git_status_accepts_uppercase_hex_commit_sha():
    assert EmpireCapabilityExecutor().verify("git_status", _valid_result(commit_sha="A" * 40)) is True


def test_git_status_rejects_failed_result():
    result = CapabilityResult(
        ok=False,
        capability="git_status",
        data={
            "branch": "main",
            "clean": True,
            "changed_files": [],
            "commit_sha": "a" * 40,
        },
        error="git failed",
    )
    assert EmpireCapabilityExecutor().verify("git_status", result) is False
