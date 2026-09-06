from pathlib import Path

from src.agent.capabilities import CapabilityResult, EmpireCapabilityExecutor


def test_project_inspection_verifier_accepts_valid_contract(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(
        ok=True,
        capability="project_inspection",
        data={"project_root": str(tmp_path.resolve()), "files": 2, "directories": 1},
        error=None,
    )
    assert executor.verify("project_inspection", result) is True


def test_project_inspection_verifier_rejects_missing_project_root(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(
        ok=True,
        capability="project_inspection",
        data={"files": 2, "directories": 1},
        error=None,
    )
    assert executor.verify("project_inspection", result) is False


def test_project_inspection_verifier_rejects_empty_project_root(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(
        ok=True,
        capability="project_inspection",
        data={"project_root": "", "files": 2, "directories": 1},
        error=None,
    )
    assert executor.verify("project_inspection", result) is False


def test_project_inspection_verifier_rejects_bool_as_files_count(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(
        ok=True,
        capability="project_inspection",
        data={"project_root": str(tmp_path.resolve()), "files": True, "directories": 1},
        error=None,
    )
    assert executor.verify("project_inspection", result) is False


def test_project_inspection_verifier_rejects_bool_as_directories_count(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(
        ok=True,
        capability="project_inspection",
        data={"project_root": str(tmp_path.resolve()), "files": 2, "directories": False},
        error=None,
    )
    assert executor.verify("project_inspection", result) is False


def test_project_inspection_verifier_rejects_negative_counts(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    negative_files = CapabilityResult(
        ok=True,
        capability="project_inspection",
        data={"project_root": str(tmp_path.resolve()), "files": -1, "directories": 1},
        error=None,
    )
    negative_directories = CapabilityResult(
        ok=True,
        capability="project_inspection",
        data={"project_root": str(tmp_path.resolve()), "files": 1, "directories": -1},
        error=None,
    )
    assert executor.verify("project_inspection", negative_files) is False
    assert executor.verify("project_inspection", negative_directories) is False


def test_project_inspection_failure_cannot_verify_as_success(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(
        ok=False,
        capability="project_inspection",
        data={"project_root": str(tmp_path.resolve()), "files": 2, "directories": 1},
        error="inspection failed",
    )
    assert executor.verify("project_inspection", result) is False
