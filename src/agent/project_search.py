"""Read-only text search capability for Empire OS projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ProjectSearchCapability:
    """Search project text without modifying files."""

    name = "project_search"
    MAX_MATCHES = 200
    MAX_LINE_LENGTH = 500

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def execute(self, task: Any = None):
        from .capabilities import CapabilityResult

        query = str(getattr(task, "description", "")).strip()
        prefix = "Execute planned step: "
        if query.lower().startswith(prefix.lower()):
            query = query[len(prefix):].strip()
        if not query:
            return CapabilityResult(False, self.name, {}, "Search query is required.")

        matches: list[dict[str, Any]] = []
        try:
            for path in self.project_root.rglob("*"):
                if len(matches) >= self.MAX_MATCHES:
                    break
                if not path.is_file() or any(part in {".git", ".pytest_cache", "__pycache__"} for part in path.parts):
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if query.lower() in line.lower():
                        matches.append({
                            "file": str(path.relative_to(self.project_root)),
                            "line": line_number,
                            "text": line[: self.MAX_LINE_LENGTH],
                        })
                        if len(matches) >= self.MAX_MATCHES:
                            break
        except OSError as exc:
            return CapabilityResult(False, self.name, {}, str(exc))

        return CapabilityResult(
            True,
            self.name,
            {"query": query, "matches": matches, "truncated": len(matches) >= self.MAX_MATCHES},
            None,
        )
