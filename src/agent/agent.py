"""
Empire OS
Digital Agent — v0.4

Purpose:
Safe local execution partner for Empire OS.

Canonical task flow:
Create → Queue → Orchestrator → Capability → Verify → Evidence → Audit
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import subprocess
import sys

from .orchestrator import EmpireOrchestrator
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

    Task creation remains owned by TaskEngine.
    Task execution is delegated to EmpireOrchestrator.
    """

    def __init__(self, project_root: str | Path, orchestrator: EmpireOrchestrator | None = None):
        self.project_root = Path(project_root).resolve()
        self.task_engine = TaskEngine()
        self.orchestrator = orchestrator or EmpireOrchestrator()

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
        return {"project_root": str(self.project_root), "file_count": len(files), "files": sorted(files)}

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
            "status": "passed" if result.returncode == 0 else "failed",
            "output": result.stdout[-4000:],
            "error": result.stderr[-2000:],
        }

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

    def process_next_task(self, approved: bool = False) -> Task | None:
        """Delegate the next queued task to the canonical orchestrator."""
        task = self.task_engine.next_pending()
        if task is None:
            return None

        plan = {
            "status": "READY",
            "plan_id": f"agent-task-{task.id}",
            "goal": task.description,
            "tasks": [{
                "id": task.id,
                "action": task.command,
                "title": task.name,
                "description": task.description,
                "requires_permission": task.requires_permission,
            }],
        }

        result = self.orchestrator.execute_plan(plan, approved=approved)
        status = result.get("status")

        if status == "rejected":
            task.reject(result.get("error") or "Task rejected.")
        elif status == "completed":
            self.task_engine.start_task(task.id)
            task_result = result.get("task_results", [{}])[0].get("result")
            self.task_engine.complete_task(task.id, task_result)
        else:
            self.task_engine.start_task(task.id)
            self.task_engine.fail_task(task.id, result.get("error") or "Task execution failed.")

        return task

    def propose(self, action: AgentAction) -> str:
        """Create a human-readable action proposal."""
        permission = "PERMISSION REQUIRED" if action.requires_permission else "AUTO-EXECUTE"
        return f"[{permission}]\nAction: {action.name}\nDescription: {action.description}"

    def approve(self, action: AgentAction, approved: bool = False) -> bool:
        """Permission boundary; API requests never block for console input."""
        if not action.requires_permission:
            return True
        return approved

    def execute(self, action: AgentAction) -> AgentResult:
        """Execute an approved direct agent action."""
        if action.executor is None:
            return AgentResult(action=action.name, status="failed", error="No executor defined.")
        try:
            return AgentResult(action=action.name, status="completed", output=action.executor())
        except Exception as exc:
            return AgentResult(action=action.name, status="failed", error=str(exc))

    def verify(self, result: AgentResult) -> bool:
        """Verify whether a direct agent action completed."""
        return result.status == "completed"

    def run_action(self, action: AgentAction, approved: bool = False) -> AgentResult:
        """Run the legacy direct-action surface; task execution remains orchestrator-owned."""
        print(self.propose(action))
        if action.requires_permission and not self.approve(action, approved=approved):
            return AgentResult(action=action.name, status="rejected")
        result = self.execute(action)
        if self.verify(result):
            print(f"\n[VERIFIED] {action.name} completed successfully.")
        else:
            print(f"\n[FAILED] {action.name}: {result.error}")
        return result


if __name__ == "__main__":
    agent = EmpireAgent(".")
    action = AgentAction(
        name="Project Inspection",
        description="Inspect the Empire OS project structure.",
        requires_permission=True,
        executor=agent.inspect_project,
    )
    result = agent.run_action(action, approved=True)
    print("\nRESULT:")
    print(result)

    def make_inspect_action(self) -> AgentAction:
        return AgentAction(
            name="Project Inspection",
            description="Inspect the Empire OS project structure.",
            requires_permission=True,
            executor=self.inspect_project,
        )

    def make_test_action(self) -> AgentAction:
        return AgentAction(
            name="Run Tests",
            description="Run the Empire OS test suite.",
            requires_permission=False,
            executor=self.run_tests,
        )
