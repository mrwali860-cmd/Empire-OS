from pathlib import Path

from src.agent.capabilities import CapabilityResult, EmpireCapabilityExecutor
from src.agent.project_search import ProjectSearchCapability
from src.agent.tasks import Task


def search_task(description: str) -> Task:
    return Task(
        id="TASK-SEARCH-001",
        name="Project search",
        description=description,
        command="project_search",
        requires_permission=False,
    )


def test_project_search_accepts_exact_query_length_boundary(tmp_path: Path):
    query = "x" * ProjectSearchCapability.MAX_QUERY_LENGTH
    (tmp_path / "app.txt").write_text(query, encoding="utf-8")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "project_search", search_task(f"Execute planned step: {query}")
    )
    assert result.ok is True
    assert result.data["query"] == query
    assert result.data["match_count"] == 1


def test_project_search_rejects_missing_project_root(tmp_path: Path):
    missing = tmp_path / "missing"
    result = EmpireCapabilityExecutor(project_root=missing).execute(
        "project_search", search_task("Execute planned step: TARGET")
    )
    assert result.ok is False
    assert result.data == {}
    assert result.error == "Project root does not exist."


def test_project_search_excludes_all_internal_directories(tmp_path: Path):
    for dirname in (".git", ".pytest_cache", "__pycache__"):
        directory = tmp_path / dirname
        directory.mkdir()
        (directory / "ignored.txt").write_text("TARGET\n", encoding="utf-8")
    (tmp_path / "visible.txt").write_text("TARGET\n", encoding="utf-8")

    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "project_search", search_task("Execute planned step: TARGET")
    )
    assert result.ok is True
    assert [match["file"] for match in result.data["matches"]] == ["visible.txt"]
    assert result.data["scanned_files"] == 1


def test_project_search_is_case_insensitive(tmp_path: Path):
    (tmp_path / "app.txt").write_text("Target value\n", encoding="utf-8")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "project_search", search_task("Execute planned step: TARGET")
    )
    assert result.ok is True
    assert result.data["match_count"] == 1
    assert result.data["matches"][0]["text"] == "Target value"


def test_project_search_caps_returned_line_at_500_chars(tmp_path: Path):
    line = "A" * (ProjectSearchCapability.MAX_LINE_LENGTH + 37)
    (tmp_path / "long.txt").write_text(line + "\n", encoding="utf-8")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "project_search", search_task("Execute planned step: A")
    )
    assert result.ok is True
    assert len(result.data["matches"][0]["text"]) == ProjectSearchCapability.MAX_LINE_LENGTH
    assert EmpireCapabilityExecutor(project_root=tmp_path).verify("project_search", result) is True


def test_project_search_verifier_rejects_line_over_500_chars(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    result = CapabilityResult(
        True,
        "project_search",
        {
            "query": "x",
            "matches": [{"file": "app.txt", "line": 1, "text": "x" * 501}],
            "match_count": 1,
            "truncated": False,
            "scanned_files": 1,
        },
        None,
    )
    assert executor.verify("project_search", result) is False


def test_project_search_verifier_rejects_invalid_scanned_files(tmp_path: Path):
    executor = EmpireCapabilityExecutor(project_root=tmp_path)
    for value in (-1, "1", None):
        result = CapabilityResult(
            True,
            "project_search",
            {
                "query": "x",
                "matches": [],
                "match_count": 0,
                "truncated": False,
                "scanned_files": value,
            },
            None,
        )
        assert executor.verify("project_search", result) is False


def test_project_search_skips_invalid_utf8_files(tmp_path: Path):
    (tmp_path / "bad.bin").write_bytes(b"TARGET\xff\n")
    (tmp_path / "good.txt").write_text("TARGET\n", encoding="utf-8")
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "project_search", search_task("Execute planned step: TARGET")
    )
    assert result.ok is True
    assert [match["file"] for match in result.data["matches"]] == ["good.txt"]
    assert result.data["scanned_files"] == 1


def test_project_search_handles_file_read_oserror(tmp_path: Path, monkeypatch):
    (tmp_path / "app.txt").write_text("TARGET\n", encoding="utf-8")
    original = Path.read_text

    def failing_read(self, *args, **kwargs):
        if self.name == "app.txt":
            raise OSError("read failed")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", failing_read)
    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "project_search", search_task("Execute planned step: TARGET")
    )
    assert result.ok is True
    assert result.data["matches"] == []
    assert result.data["scanned_files"] == 0


def test_project_search_skips_symlink_escape(tmp_path: Path):
    outside = tmp_path.parent / "empire-search-outside.txt"
    outside.write_text("TARGET\n", encoding="utf-8")
    try:
        (tmp_path / "escape.txt").symlink_to(outside)
    except (OSError, NotImplementedError):
        return
    try:
        result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
            "project_search", search_task("Execute planned step: TARGET")
        )
        assert result.ok is True
        assert result.data["matches"] == []
    finally:
        outside.unlink(missing_ok=True)


def test_project_search_is_read_only(tmp_path: Path):
    target = tmp_path / "app.txt"
    target.write_text("TARGET\n", encoding="utf-8")
    before = {path.relative_to(tmp_path): path.stat().st_mtime_ns for path in tmp_path.rglob("*")}

    result = EmpireCapabilityExecutor(project_root=tmp_path).execute(
        "project_search", search_task("Execute planned step: TARGET")
    )

    after = {path.relative_to(tmp_path): path.stat().st_mtime_ns for path in tmp_path.rglob("*")}
    assert result.ok is True
    assert before == after
    assert target.read_text(encoding="utf-8") == "TARGET\n"
