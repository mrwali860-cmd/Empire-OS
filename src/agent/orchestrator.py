"""
Empire OS
Task Orchestrator — v0.14

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

    MAX_TASKS = 100
    MAX_PLAN_ID_CHARS = 200
    MAX_GOAL_CHARS = 2_000
    MAX_TASK_TEXT_CHARS = 2_000

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
        if not isinstance(task, Task):
            raise TypeError("Task must be a Task instance.")
        return task.command

    def route(self, task: Task) -> RouteDecision:
        command = self.classify(task)
        capability = self.routes.get(command)
        if capability is None:
            return RouteDecision(task.id, command, "unknown", False, f"No capability registered for command: {command}")
        if not self.capability_executor.registry.has(capability):
            return RouteDecision(task.id, command, capability, False, f"Capability is not registered: {capability}")
        return RouteDecision(task.id, command, capability, True, "Route accepted.")

    @classmethod
    def _task_from_plan(cls, raw: dict[str, Any]) -> Task:
        if not isinstance(raw, dict):
            raise TypeError("Task must be a dictionary.")
        task_id = raw.get("id")
        action = raw.get("action")
        title = raw.get("title", task_id)
        description = raw.get("description", "")
        requires_permission = raw.get("requires_permission", True)
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("Task ID must be a non-empty string.")
        if not isinstance(action, str) or not action.strip():
            raise ValueError("Task action must be a non-empty string.")
        if not isinstance(title, str):
            raise TypeError("Task title must be a string.")
        if not isinstance(description, str):
            raise TypeError("Task description must be a string.")
        if len(title) > cls.MAX_TASK_TEXT_CHARS:
            raise ValueError("Task title exceeds 2000 characters.")
        if len(description) > cls.MAX_TASK_TEXT_CHARS:
            raise ValueError("Task description exceeds 2000 characters.")
        if type(requires_permission) is not bool:
            raise TypeError("Task requires_permission must be a boolean.")
        return Task(
            id=task_id,
            name=title,
            description=description,
            command=action,
            requires_permission=requires_permission,
        )

    @staticmethod
    def _evidence(output: Any) -> dict[str, Any] | None:
        if isinstance(output, CapabilityResult):
            return output.to_dict()
        return None

    @classmethod
    def _validate_plan(cls, plan: Any) -> str | None:
        if not isinstance(plan, dict):
            return "Plan must be a dictionary."
        if plan.get("status") != "READY":
            return "Plan is not READY."
        plan_id = plan.get("plan_id")
        if not isinstance(plan_id, str) or not plan_id.strip():
            return "Plan must include a non-empty plan_id."
        if len(plan_id) > cls.MAX_PLAN_ID_CHARS:
            return "Plan ID exceeds 200 characters."
        goal = plan.get("goal", "")
        if not isinstance(goal, str):
            return "Plan goal must be a string."
        if len(goal) > cls.MAX_GOAL_CHARS:
            return "Plan goal exceeds 2000 characters."
        tasks = plan.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            return "Plan must include at least one task."
        if len(tasks) > cls.MAX_TASKS:
            return "Plan cannot contain more than 100 tasks."
        seen_ids: set[str] = set()
        for index, raw in enumerate(tasks, start=1):
            if not isinstance(raw, dict):
                return f"Task {index} must be a dictionary."
            task_id = raw.get("id")
            action = raw.get("action")
            if not isinstance(task_id, str) or not task_id.strip():
                return f"Task {index} is missing required field(s): id."
            if not isinstance(action, str) or not action.strip():
                return f"Task {index} is missing required field(s): action."
            if task_id in seen_ids:
                return f"Duplicate task id: {task_id}"
            seen_ids.add(task_id)
            title = raw.get("title", task_id)
            description = raw.get("description", "")
            requires_permission = raw.get("requires_permission", True)
            if not isinstance(title, str):
                return f"Task {index} title must be a string."
            if not isinstance(description, str):
                return f"Task {index} description must be a string."
            if len(title) > cls.MAX_TASK_TEXT_CHARS:
                return f"Task {index} title exceeds 2000 characters."
            if len(description) > cls.MAX_TASK_TEXT_CHARS:
                return f"Task {index} description exceeds 2000 characters."
            if type(requires_permission) is not bool:
                return f"Task {index} requires_permission must be a boolean."
        return None

    def _verify_output(self, capability: str, output: Any, verifier, task: Task, *, injected_executor: bool) -> bool:
        if verifier is not None:
            return bool(verifier(task, output))
        if injected_executor and isinstance(output, dict):
            return bool(output.get("ok", False))
        return self.capability_executor.verify(capability, output)

    def _audit(self, task: Task, capability: str, status: str, verified: bool, output: Any = None, error: str | None = None) -> None:
        self.audit.record(AuditRecord(task.id, task.command, capability, status, verified, error, self._evidence(output)))

    def _result(self, *, status: str, plan_id: Any, goal: Any, tasks: list[Task], completed_tasks: int, failed_task_id: str | None, error: str | None, capability_results: list[dict[str, Any]]) -> dict[str, Any]:
        return {"status": status, "plan_id": plan_id, "goal": goal, "completed_tasks": completed_tasks, "failed_task_id": failed_task_id, "error": error, "current_task": next((task.id for task in tasks if task.status.value == "running"), None), "task_results": [task.to_dict() for task in tasks], "capability_results": capability_results, "audit": self.audit.as_dicts()}

    def execute_plan(self, plan: dict[str, Any], *, executor: Callable[[Task], Any] | None = None, verifier: Callable[[Task, Any], bool] | None = None, approved: bool = False) -> dict[str, Any]:
        self.audit.clear()
        if executor is not None and not callable(executor):
            return self._result(status=OrchestrationStatus.FAILED.value, plan_id=None, goal="", tasks=[], completed_tasks=0, failed_task_id=None, error="Executor must be callable.", capability_results=[])
        if verifier is not None and not callable(verifier):
            return self._result(status=OrchestrationStatus.FAILED.value, plan_id=None, goal="", tasks=[], completed_tasks=0, failed_task_id=None, error="Verifier must be callable.", capability_results=[])
        if type(approved) is not bool:
            return self._result(status=OrchestrationStatus.FAILED.value, plan_id=None, goal="", tasks=[], completed_tasks=0, failed_task_id=None, error="approved must be a boolean.", capability_results=[])
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
                task.reject(route.reason)
                self._audit(task, route.capability, "rejected", False, error=route.reason)
                return self._result(status=OrchestrationStatus.REJECTED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=route.reason, capability_results=capability_results)
            if task.requires_permission and not approved:
                error = "Permission not approved."
                task.reject(error)
                self._audit(task, route.capability, "rejected", False, error=error)
                return self._result(status=OrchestrationStatus.REJECTED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=error, capability_results=capability_results)
            try:
                task.start()
                output = executor(task) if executor is not None else self.capability_executor.execute(route.capability, task)
                evidence = self._evidence(output)
                if evidence is not None:
                    capability_results.append(evidence)
                verified = self._verify_output(route.capability, output, verifier, task, injected_executor=executor is not None)
                if not verified:
                    error = "Task verification failed."
                    task.fail(error)
                    self._audit(task, route.capability, "failed", False, output, error)
                    return self._result(status=OrchestrationStatus.FAILED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=error, capability_results=capability_results)
                task.complete(output)
                self._audit(task, route.capability, "completed", True, output)
                completed_tasks += 1
            except Exception as exc:
                task.fail(str(exc))
                self._audit(task, route.capability, "failed", False, error=str(exc))
                return self._result(status=OrchestrationStatus.FAILED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=str(exc), capability_results=capability_results)
        return self._result(status=OrchestrationStatus.COMPLETED.value, plan_id=plan.get("plan_id"), goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=None, error=None, capability_results=capability_results)
