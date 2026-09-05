"""Bounded read-only file content capability for Empire OS."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FileReadCapability:
    """Read a project file without modifying the filesystem."""

    name = "file_read"
    MAX_BYTES = 1_000_000
    MAX_CHARS = 20_000

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    @staticmethod
    def _extract_path(description: str) -> str:
        query = description.strip()
        prefix = "Execute planned step: "
        if query.lower().startswith(prefix.lower()):
            query = query[len(prefix):].strip()
        markers = ("read file:", "read file ", "open file:", "open file ")
        lower_query = query.lower()
        for marker in markers:
            if lower_query.startswith(marker):
                return query[len(marker):].strip()
        return query

    def execute(self, task: Any = None):
        from .capabilities import CapabilityResult

        requested = self._extract_path(str(getattr(task, "description", "")))
        if not requested:
            return CapabilityResult(False, self.name, {}, "File path is required.")

        candidate = (self.project_root / requested).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError:
            return CapabilityResult(False, self.name, {}, "File path is outside the project root.")

        if candidate.is_symlink() or not candidate.is_file():
            return CapabilityResult(False, self.name, {}, "File does not exist or is not a regular file.")

        try:
            if candidate.stat().st_size > self.MAX_BYTES:
                return CapabilityResult(False, self.name, {}, "File exceeds the read size limit.")
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return CapabilityResult(False, self.name, {}, str(exc))

        truncated = len(text) > self.MAX_CHARS
        return CapabilityResult(
            True,
            self.name,
            {
                "path": str(candidate.relative_to(self.project_root)),
                "content": text[: self.MAX_CHARS],
                "char_count": len(text),
                "truncated": truncated,
            },
            None,
        )
