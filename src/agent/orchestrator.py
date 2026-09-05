"""
Empire OS
Task Orchestrator — v0.2

Purpose:
Coordinate a validated execution plan without embedding capability logic.

Flow:

Plan → Route → Permission → Execute → Verify → Next Task
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .tasks import Task


class OrchestrationStatus(str, Enum):
    """Lifecycle state of a plan execution."""

    READY = "ready"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """Routing decision made for a task."""

    task_id: str
    command: str
    capability: str
    accepted: bool
    reason: str


class EmpireOrchestrator:
    """
    Deterministic coordinator for Empire OS.

    The orchestrator owns sequencing and safety boundaries. It does not
    implement capabilities itself; execution and verification are injected.
    """

    def __init__(self) -> None:
        self.routes: dict[str, str] = {
            "inspect_project": "project_inspection",
            "run_tests": "test_runner",
        }

    def classify(self, task: Task) -> str:
        """Return the task command."""
        return task.command

    def route(self, task: Task) -> RouteDecision:
        """Decide which capability should handle a task."""
        command = self.classify(task)
        capability = self.routes.get(command)

        if capability is None:
            return RouteDecision(
                task_id=task.id,
                command=command,
                capability="",
                accepted=False,
                reason=f"No capability registered for command: {command}",
            )

        return RouteDecision(
            task_id=task.id,
            command=command,
            capability=capability,
            accepted=True,
            reason="Route accepted.",
        )

    @staticmethod
    def _task_from_plan(raw: dict[str, Any]) -> Task:
        """Convert a planner task contract into an executable Task."""
        return Task(
            id=str(raw["id"]),
            name=str(raw.get("title", raw["id"])),
            description=str(raw.get("description", "")),
            command=str(raw.get("action", "")),
            requires_permission=bool(raw.get("requires_permission", True)),
        )

    def execute_plan(
        self,
        plan: dict[str, Any],
        *,
        executor: Callable[[Task], Any],
        verifier: Callable[[Task, Any], bool] | None = None,
        approved: bool = False,
    ) -> dict[str, Any]:
        """
        Execute plan tasks sequentially and stop at the first failure.

        The executor is deliberately injected so the orchestrator remains
        independent from concrete agents and external side effects.
        """
        if plan.get("status") != "READY":
            return {
                "status": OrchestrationStatus.FAILED.value,
                "plan_id": plan.get("plan_id"),
                "goal": plan.get("goal", ""),
                "completed_tasks": 0,
                "failed_task_id": None,
                "error": "Plan is not READY.",
            }

        tasks = [self._task_from_plan(raw) for raw in plan.get("tasks", [])]
        result = {
            "status": OrchestrationStatus.RUNNING.value,
            "plan_id": plan.get("plan_id"),
            "goal": plan.get("goal", ""),
            "completed_tasks": 0,
            "failed_task_id": None,
            "error": None,
        }

        for task in tasks:
            route = self.route(task)
            if not route.accepted:
                result.update(
                    status=OrchestrationStatus.FAILED.value,
                    failed_task_id=task.id,
                    error=route.reason,
                )
                return result

            if task.requires_permission and not approved:
                result.update(
                    status=OrchestrationStatus.REJECTED.value,
                    failed_task_id=task.id,
                    error="Permission not approved.",
                )
                return result

            try:
                result["status"] = OrchestrationStatus.RUNNING.value
                output = executor(task)
                result["status"] = OrchestrationStatus.VERIFYING.value

                verified = (
                    verifier(task, output)
                    if verifier is not None
                    else output is not None
                )
                if not verified:
                    result.update(
                        status=OrchestrationStatus.FAILED.value,
                        failed_task_id=task.id,
                        error="Task verification failed.",
                    )
                    return result

                result["completed_tasks"] += 1

            except Exception as exc:
                result.update(
                    status=OrchestrationStatus.FAILED.value,
                    failed_task_id=task.id,
                    error=str(exc),
                )
                return result

        result["status"] = OrchestrationStatus.COMPLETED.value
        return result
