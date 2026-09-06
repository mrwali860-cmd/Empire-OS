"""Permission-gated file write capability for Empire OS."""

from __future__ import annotations

import os
import tempfile
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
        text = description
        prefix = "Execute planned step: "
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):]
        marker = "write file:"
        if not text.lstrip().lower().startswith(marker):
            return "", ""
        leading = len(text) - len(text.lstrip())
        text = text[leading + len(marker):]
        separator = " content:"
        index = text.lower().find(separator)
        if index < 0:
            return text.strip(), ""
        path_text = text[:index].strip()
        content = text[index + len(separator):]
        if content.startswith(" "):
            content = content[1:]
        return path_text, content

    @classmethod
    def validate_task(cls, task: Any) -> bool:
        """Validate the minimum file-write input contract before execution."""
        description = str(getattr(task, "description", ""))
        path_text, _ = cls._extract_request(description)
        return bool(path_text)

    def execute(self, task: Any = None):
        from .capabilities import CapabilityResult

        path_text, content = self._extract_request(str(getattr(task, "description", "")))
        if not path_text:
            return CapabilityResult(False, self.name, {}, "File path is required.")

        lexical_candidate = self.project_root / path_text
        if lexical_candidate.is_symlink():
            return CapabilityResult(False, self.name, {}, "Symlink targets are not allowed.")

        candidate = lexical_candidate.resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError:
            return CapabilityResult(False, self.name, {}, "File path is outside the project root.")
        if candidate == self.project_root:
            return CapabilityResult(False, self.name, {}, "Target must be a regular file inside the project root.")

        try:
            encoded = content.encode("utf-8")
        except UnicodeEncodeError as exc:
            return CapabilityResult(False, self.name, {}, str(exc))
        if len(encoded) > self.MAX_BYTES:
            return CapabilityResult(False, self.name, {}, "File exceeds the write size limit.")

        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(prefix=f".{candidate.name}.", dir=candidate.parent)
            try:
                with os.fdopen(fd, "wb") as temp_file:
                    temp_file.write(encoded)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                os.replace(temp_name, candidate)
            except Exception:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass
                raise
        except OSError as exc:
            return CapabilityResult(False, self.name, {}, str(exc))

        return CapabilityResult(
            True,
            self.name,
            {"path": str(candidate.relative_to(self.project_root)), "bytes_written": len(encoded)},
            None,
        )
