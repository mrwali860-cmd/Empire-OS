"""Production-grade, read-only text search capability for Empire OS projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ProjectSearchCapability:
    """Search project text with bounded, deterministic, auditable results."""

    name = "project_search"
    MAX_MATCHES = 200
    MAX_LINE_LENGTH = 500
    MAX_QUERY_LENGTH = 200
    EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__"}

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    @staticmethod
    def _extract_query(description: str) -> str:
        query = description.strip()
        prefix = "Execute planned step: "
        if query.lower().startswith(prefix.lower()):
            query = query[len(prefix):].strip()

        marker = " for:"
        lower_query = query.lower()
        marker_index = lower_query.find(marker)
        if marker_index >= 0:
            query = query[marker_index + len(marker):].strip()

        return query

    def execute(self, task: Any = None):
        from .capabilities import CapabilityResult

        description = str(getattr(task, "description", ""))
        query = self._extract_query(description)
        if not query:
            return CapabilityResult(False, self.name, {}, "Search query is required.")
        if len(query) > self.MAX_QUERY_LENGTH:
            return CapabilityResult(False, self.name, {}, f"Search query exceeds {self.MAX_QUERY_LENGTH} characters.")
        if not self.project_root.is_dir():
            return CapabilityResult(False, self.name, {}, "Project root does not exist.")

        matches: list[dict[str, Any]] = []
        scanned_files = 0
        truncated = False
        query_lower = query.lower()

        try:
            for path in sorted(self.project_root.rglob("*"), key=lambda item: str(item)):
                if not path.is_file() or any(part in self.EXCLUDED_PARTS for part in path.parts):
                    continue
                try:
                    resolved = path.resolve()
                    resolved.relative_to(self.project_root)
                except (OSError, ValueError):
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue

                scanned_files += 1
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if query_lower not in line.lower():
                        continue
                    if len(matches) >= self.MAX_MATCHES:
                        truncated = True
                        break
                    matches.append(
                        {
                            "file": str(path.relative_to(self.project_root)),
                            "line": line_number,
                            "text": line[: self.MAX_LINE_LENGTH],
                        }
                    )
                if truncated:
                    break
        except OSError as exc:
            return CapabilityResult(False, self.name, {}, str(exc))

        return CapabilityResult(
            True,
            self.name,
            {
                "query": query,
                "matches": matches,
                "match_count": len(matches),
                "truncated": truncated,
                "scanned_files": scanned_files,
            },
            None,
        )
