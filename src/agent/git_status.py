"""Read-only Git status capability for Empire OS."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


class GitStatusCapability:
    """Inspect repository state without mutating the working tree."""

    name = "git_status"

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def execute(self, task: Any = None):
        """Return branch, cleanliness, changed files, and current commit SHA."""
        from .capabilities import CapabilityResult

        try:
            branch = self._git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
            commit_sha = self._git(["rev-parse", "HEAD"]).strip()
            porcelain = self._git(["status", "--porcelain"])
        except (OSError, subprocess.CalledProcessError) as exc:
            return CapabilityResult(
                ok=False,
                capability=self.name,
                data=None,
                error=str(exc),
            )

        changed_files = [line[3:] for line in porcelain.splitlines() if len(line) >= 4]
        data = {
            "branch": branch,
            "clean": not changed_files,
            "changed_files": changed_files,
            "commit_sha": commit_sha,
        }
        return CapabilityResult(ok=True, capability=self.name, data=data, error=None)

    def _git(self, args: list[str]) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.rstrip("\r\n")
