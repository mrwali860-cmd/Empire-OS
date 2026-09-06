from pathlib import Path

from src.agent.capabilities import EmpireCapabilityExecutor
from src.agent.tasks import Task


def task(command: str, description: str) -> Task:
    return Task(
        id="TASK-SECURITY-001",
        name="Path security",
        description=description,
        command=command,
        requires_permission=False,
    )


def test_file_read_rejects_symlink_target_before_resolution(tmp_path: Path):
    target = tmp_path / "real.txt"
    target.write_text("secret", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        return

    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_read", task("file_read", "Execute planned step: read file: link.txt")
    )
    assert result.ok is False
    assert "symlink" in result.error.lower()


def test_file_write_rejects_symlink_target_before_resolution(tmp_path: Path):
    target = tmp_path / "real.txt"
    target.write_text("original", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        return

    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "file_write", task("file_write", "Execute planned step: write file: link.txt content: changed")
    )
    assert result.ok is False
    assert "symlink" in result.error.lower()
    assert target.read_text(encoding="utf-8") == "original"
