"""
Empire OS
Digital Agent — v0.3

Purpose:
Safe local execution partner for Empire OS.

Flow:
Observe → Decide → Permission → Execute → Verify

Task Engine:
Create → Queue → Run → Verify → Complete/Fail
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import subprocess
import sys

from .tasks import Task
from .task_engine import TaskEngine


@dataclass(slots=True)
class AgentAction:
    """An explicitly executable agent action."""

    name: str
    description: str
    requires_permission: bool = True
    executor: Callable[[], object] | None = None


@dataclass(slots=True)
class AgentResult:
    """Result returned after an agent action."""

    action: str
    status: str
    output: object | None = None
    error: str | None = None


class EmpireAgent:
    """
    Safe local agent for Empire OS.

    Current capabilities:

    - Inspect project
    - Run tests
    - Create tasks
    - Process queued tasks
    - Execute approved actions
    - Verify results
    """

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.task_engine = TaskEngine()

    # =================================================
    # OBSERVE
    # =================================================

    def inspect_project(self) -> dict[str, object]:
        """Inspect the current Empire OS project."""

        files = [
            str(path.relative_to(self.project_root))
            for path in self.project_root.rglob("*")
            if (
                path.is_file()
                and ".git" not in path.parts
                and "__pycache__" not in path.parts
                and ".pytest_cache" not in path.parts
                and ".ruff_cache" not in path.parts
                and ".venv" not in path.parts
            )
        ]

        return {
            "project_root": str(self.project_root),
            "file_count": len(files),
            "files": sorted(files),
        }

    # =================================================
    # TEST
    # =================================================

    def run_tests(self) -> dict[str, object]:
        """Run the Empire OS test suite."""

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        return {
            "return_code": result.returncode,
            "status": (
                "passed"
                if result.returncode == 0
                else "failed"
            ),
            "output": result.stdout[-4000:],
            "error": result.stderr[-2000:],
        }

    # =================================================
    # TASK CREATION
    # =================================================

    def create_task(
        self,
        task_id: str,
        name: str,
        description: str,
        command: str,
        requires_permission: bool = True,
    ) -> Task:
        """Create and queue a new Empire OS task."""

        task = Task(
            id=task_id,
            name=name,
            description=description,
            command=command,
            requires_permission=requires_permission,
        )

        return self.task_engine.add_task(task)

    # =================================================
    # TASK PROCESSING
    # =================================================

    def process_next_task(
        self,
        approved: bool = False,
    ) -> Task | None:
        """
        Process the next pending task.

        Supported commands:

        - inspect_project
        - run_tests
        """

        task = self.task_engine.next_pending()

        if task is None:
            return None

        # ---------------------------------------------
        # Permission
        # ---------------------------------------------

        if task.requires_permission and not approved:
            task.reject(
                "Permission not approved."
            )
            return task

        # ---------------------------------------------
        # Start
        # ---------------------------------------------

        self.task_engine.start_task(task.id)

        # ---------------------------------------------
        # Execute
        # ---------------------------------------------

        try:

            if task.command == "inspect_project":

                result = self.inspect_project()

            elif task.command == "run_tests":

                result = self.run_tests()

            else:

                self.task_engine.fail_task(
                    task.id,
                    (
                        "Unknown task command: "
                        f"{task.command}"
                    ),
                )

                return task

            # -----------------------------------------
            # Complete
            # -----------------------------------------

            self.task_engine.complete_task(
                task.id,
                result,
            )

        except Exception as exc:

            self.task_engine.fail_task(
                task.id,
                str(exc),
            )

        return task

    # =================================================
    # DECIDE
    # =================================================

    def propose(
        self,
        action: AgentAction,
    ) -> str:
        """Create a human-readable action proposal."""

        permission = (
            "PERMISSION REQUIRED"
            if action.requires_permission
            else "AUTO-EXECUTE"
        )

        return (
            f"[{permission}]\n"
            f"Action: {action.name}\n"
            f"Description: {action.description}"
        )

    # =================================================
    # PERMISSION
    # =================================================

    def approve(
        self,
        action: AgentAction,
        approved: bool = False,
    ) -> bool:
        """
        Permission boundary.

        API requests must never block waiting for
        console input.
        """

        if not action.requires_permission:
            return True

        return approved

    # =================================================
    # EXECUTE
    # =================================================

    def execute(
        self,
        action: AgentAction,
    ) -> AgentResult:
        """Execute an approved action."""

        if action.executor is None:

            return AgentResult(
                action=action.name,
                status="failed",
                error="No executor defined.",
            )

        try:

            output = action.executor()

            return AgentResult(
                action=action.name,
                status="completed",
                output=output,
            )

        except Exception as exc:

            return AgentResult(
                action=action.name,
                status="failed",
                error=str(exc),
            )

    # =================================================
    # VERIFY
    # =================================================

    def verify(
        self,
        result: AgentResult,
    ) -> bool:
        """Verify whether an action completed."""

        return result.status == "completed"

    # =================================================
    # ACTION PIPELINE
    # =================================================

    def run_action(
        self,
        action: AgentAction,
        approved: bool = False,
    ) -> AgentResult:
        """
        Run:

        Decide → Permission → Execute → Verify
        """

        print(self.propose(action))

        if action.requires_permission:

            if not self.approve(
                action,
                approved=approved,
            ):

                return AgentResult(
                    action=action.name,
                    status="rejected",
                )

        result = self.execute(action)

        if self.verify(result):

            print(
                f"\n[VERIFIED] "
                f"{action.name} completed successfully."
            )

        else:

            print(
                f"\n[FAILED] "
                f"{action.name}: {result.error}"
            )

        return result


# =====================================================
# DIRECT EXECUTION
# =====================================================

if __name__ == "__main__":

    agent = EmpireAgent(".")

    # -----------------------------------------------
    # Example: direct project inspection
    # -----------------------------------------------

    action = AgentAction(
        name="Project Inspection",
        description=(
            "Inspect the Empire OS project structure."
        ),
        requires_permission=True,
        executor=agent.inspect_project,
    )

    result = agent.run_action(
        action,
        approved=True,
    )

    print("\nRESULT:")
    print(result)
    # -------------------------------------------------
    # Action Factories
    # -------------------------------------------------

    def make_inspect_action(self) -> AgentAction:
        """Create a project-inspection action."""

        return AgentAction(
            name="Project Inspection",
            description="Inspect the Empire OS project structure.",
            requires_permission=True,
            executor=self.inspect_project,
        )

    def make_test_action(self) -> AgentAction:
        """Create a test-suite action."""

        return AgentAction(
            name="Run Tests",
            description="Run the Empire OS test suite.",
            requires_permission=False,
            executor=self.run_tests,
        )