"""
Empire OS
Task Orchestrator — v0.4

Flow:
Plan → Route → Permission → Execute → Verify → Next Task
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .capabilities import EmpireCapabilityExecutor
from .tasks import Task


class OrchestrationStatus(str, Enum):
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
    """Deterministic coordinator backed by an allow-listed capability layer."""

    def __init__(self, capability_executor=None) -> None:
        self.routes: dict[str, str] = {
            "inspect_project": "project_inspection",
            "run_tests": "test_runner",
        }
        self.capability_executor = capability_executor or EmpireCapabilityExecutor()

    def classify(self, task: Task) -> str:
        return task.command

    def route(self, task: Task) -> RouteDecision:
        command = self.classify(task)
        capability = self.routes.get(command)
        if capability is None:
            return RouteDecision(task.id, command, "", False, f"No capability registered for command: {command}")
        if not self.capability_executor.registry.has(capability):
            return RouteDecision(task.id, command, capability, False, f"Capability is not registered: {capability}")
        return RouteDecision(task.id, command, capability, True, "Route accepted.")

    @staticmethod
    def _task_from_plan(raw: dict[str, Any]) -> Task:
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
        executor: Callable[[Task], Any] | None = None,
        verifier: Callable[[Task, Any], bool] | None = None,
        approved: bool = False,
    ) -> dict[str, Any]:
        """Execute tasks sequentially and verify capability evidence."""
        if plan.get("status") != "READY":
            return {"status": "failed", "plan_id": plan.get("plan_id"), "goal": plan.get("goal", ""), "completed_tasks": 0, "failed_task_id": None, "error": "Plan is not READY."}

        tasks = [self._task_from_plan(raw) for raw in plan.get("tasks", [])]
        result = {"status": "running", "plan_id": plan.get("plan_id"), "goal": plan.get("goal", ""), "completed_tasks": 0, "failed_task_id": None, "error": None}

        for task in tasks:
            route = self.route(task)
            if not route.accepted:
                result.update(status="rejected", failed_task_id=task.id, error=route.reason)
                return result
            if task.requires_permission and not approved:
                result.update(status="rejected", failed_task_id=task.id, error="Permission not approved.")
                return result

            try:
                task.start()
                output = executor(task) if executor is not None else self.capability_executor.execute(route.capability, task)
                result["status"] = "verifying"
                if verifier is not None:
                    verified = verifier(task, output)
                elif hasattr(self.capability_executor, "verify"):
                    verified = self.capability_executor.verify(route.capability, output)
                else:
                    verified = output is not None
                if not verified:
                    task.fail("Task verification failed.")
                    result.update(status="failed", failed_task_id=task.id, error="Task verification failed.")
                    return result
                task.complete(output)
                result["completed_tasks"] += 1
            except Exception as exc:
                task.fail(str(exc))
                result.update(status="failed", failed_task_id=task.id, error=str(exc))
                return result

        result["status"] = "completed"
        return result
