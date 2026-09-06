"""
Empire OS
Task Orchestrator — v0.13

Flow:
Plan → Validate → Route → Permission → Execute → Verify → Evidence → Audit → Next Task
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .audit import AuditRecord, ExecutionAudit
from .capabilities import CapabilityResult, EmpireCapabilityExecutor
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
    task_id: str
    command: str
    capability: str
    accepted: bool
    reason: str


class EmpireOrchestrator:
    """Deterministic coordinator backed by explicit capability contracts."""

    def __init__(self, capability_executor=None, audit=None) -> None:
        self.routes: dict[str, str] = {
            "file_read": "file_read",
            "file_write": "file_write",
            "inspect_project": "project_inspection",
            "project_search": "project_search",
            "run_tests": "test_runner",
            "git_status": "git_status",
            "decision_engine": "decision_engine",
        }
        self.capability_executor = capability_executor or EmpireCapabilityExecutor()
        self.audit = audit or ExecutionAudit()

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
        return Task(id=str(raw["id"]), name=str(raw.get("title", raw["id"])), description=str(raw.get("description", "")), command=str(raw.get("action", "")), requires_permission=bool(raw.get("requires_permission", True)))

    @staticmethod
    def _evidence(output: Any) -> dict[str, Any] | None:
        if isinstance(output, CapabilityResult):
            return output.to_dict()
        return None

    @staticmethod
    def _validate_plan(plan: Any) -> str | None:
        if not isinstance(plan, dict): return "Plan must be a dictionary."
        if plan.get("status") != "READY": return "Plan is not READY."
        if not isinstance(plan.get("plan_id"), str) or not plan["plan_id"].strip(): return "Plan must include a non-empty plan_id."
        tasks = plan.get("tasks")
        if not isinstance(tasks, list) or not tasks: return "Plan must include at least one task."
        seen_ids: set[str] = set()
        for index, raw in enumerate(tasks, start=1):
            if not isinstance(raw, dict): return f"Task {index} must be a dictionary."
            missing = [key for key in ("id", "action") if not str(raw.get(key, "")).strip()]
            if missing: return f"Task {index} is missing required field(s): {', '.join(missing)}."
            task_id = str(raw["id"])
            if task_id in seen_ids: return f"Duplicate task id: {task_id}"
            seen_ids.add(task_id)
        return None

    def _verify_output(self, capability: str, output: Any, verifier, task: Task, *, injected_executor: bool) -> bool:
        if verifier is not None: return bool(verifier(task, output))
        if injected_executor and isinstance(output, dict): return bool(output.get("ok", False))
        return self.capability_executor.verify(capability, output)

    def _audit(self, task: Task, capability: str, status: str, verified: bool, output: Any = None, error: str | None = None) -> None:
        self.audit.record(AuditRecord(task.id, task.command, capability, status, verified, error, self._evidence(output)))

    def _result(self, *, status: str, plan_id: Any, goal: Any, tasks: list[Task], completed_tasks: int, failed_task_id: str | None, error: str | None, capability_results: list[dict[str, Any]]) -> dict[str, Any]:
        return {"status": status, "plan_id": plan_id, "goal": goal, "completed_tasks": completed_tasks, "failed_task_id": failed_task_id, "error": error, "current_task": next((task.id for task in tasks if task.status.value == "running"), None), "task_results": [task.to_dict() for task in tasks], "capability_results": capability_results, "audit": self.audit.as_dicts()}

    def execute_plan(self, plan: dict[str, Any], *, executor: Callable[[Task], Any] | None = None, verifier: Callable[[Task, Any], bool] | None = None, approved: bool = False) -> dict[str, Any]:
        self.audit.clear()
        validation_error = self._validate_plan(plan)
        if validation_error:
            plan_id = plan.get("plan_id") if isinstance(plan, dict) else None
            goal = plan.get("goal", "") if isinstance(plan, dict) else ""
            return self._result(status=OrchestrationStatus.FAILED.value, plan_id=plan_id, goal=goal, tasks=[], completed_tasks=0, failed_task_id=None, error=validation_error, capability_results=[])
        tasks = [self._task_from_plan(raw) for raw in plan["tasks"]]
        capability_results: list[dict[str, Any]] = []
        completed_tasks = 0
        for task in tasks:
            route = self.route(task)
            if not route.accepted:
                task.reject(route.reason); self._audit(task, route.capability, "rejected", False, error=route.reason)
                return self._result(status=OrchestrationStatus.REJECTED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=route.reason, capability_results=capability_results)
            if task.requires_permission and not approved:
                error = "Permission not approved."; task.reject(error); self._audit(task, route.capability, "rejected", False, error=error)
                return self._result(status=OrchestrationStatus.REJECTED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=error, capability_results=capability_results)
            try:
                task.start(); output = executor(task) if executor is not None else self.capability_executor.execute(route.capability, task)
                evidence = self._evidence(output)
                if evidence is not None: capability_results.append(evidence)
                verified = self._verify_output(route.capability, output, verifier, task, injected_executor=executor is not None)
                if not verified:
                    error = "Task verification failed."; task.fail(error); self._audit(task, route.capability, "failed", False, output, error)
                    return self._result(status=OrchestrationStatus.FAILED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=error, capability_results=capability_results)
                task.complete(output); self._audit(task, route.capability, "completed", True, output); completed_tasks += 1
            except Exception as exc:
                task.fail(str(exc)); self._audit(task, route.capability, "failed", False, error=str(exc))
                return self._result(status=OrchestrationStatus.FAILED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=str(exc), capability_results=capability_results)
        return self._result(status=OrchestrationStatus.COMPLETED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=None, error=None, capability_results=capability_results)
