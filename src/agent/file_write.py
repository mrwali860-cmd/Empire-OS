"""Permission-gated file write capability for Empire OS."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FileWriteCapability:
    """Write bounded UTF-8 text files inside the project root."""

    name = "file_write"
    MAX_BYTES = 1_000_000

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    @staticmethod
    def _extract_request(description: str) -> tuple[str, str]:
        text = description.strip()
        prefix = "Execute planned step: "
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
        marker = "write file:"
        if not text.lower().startswith(marker):
            return "", ""
        text = text[len(marker):].strip()
        separator = " content:"
        lower = text.lower()
        index = lower.find(separator)
        if index < 0:
            return text, ""
        return text[:index].strip(), text[index + len(separator):].lstrip()

    def execute(self, task: Any = None):
        from .capabilities import CapabilityResult

        path_text, content = self._extract_request(str(getattr(task, "description", "")))
        if not path_text:
            return CapabilityResult(False, self.name, {}, "File path is required.")
        candidate = (self.project_root / path_text).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError:
            return CapabilityResult(False, self.name, {}, "File path is outside the project root.")
        if candidate.is_symlink() or candidate == self.project_root:
            return CapabilityResult(False, self.name, {}, "Target must be a regular file inside the project root.")
        try:
            encoded = content.encode("utf-8")
        except UnicodeEncodeError as exc:
            return CapabilityResult(False, self.name, {}, str(exc))
        if len(encoded) > self.MAX_BYTES:
            return CapabilityResult(False, self.name, {}, "File exceeds the write size limit.")
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(content, encoding="utf-8")
        except OSError as exc:
            return CapabilityResult(False, self.name, {}, str(exc))
        return CapabilityResult(
            True,
            self.name,
            {"path": str(candidate.relative_to(self.project_root)), "bytes_written": len(encoded)},
            None,
        )
