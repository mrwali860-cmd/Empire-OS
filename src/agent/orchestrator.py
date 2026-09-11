"""Empire OS task orchestration with auditable request identity."""

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
    MAX_TASKS = 100
    MAX_PLAN_ID_CHARS = 200
    MAX_GOAL_CHARS = 2_000
    MAX_TASK_TEXT_CHARS = 2_000
    MAX_REQUEST_ID_CHARS = 200

    def __init__(self, capability_executor=None, audit=None) -> None:
        self.routes = {"file_read": "file_read", "file_write": "file_write", "inspect_project": "project_inspection", "project_search": "project_search", "run_tests": "test_runner", "git_status": "git_status", "decision_engine": "decision_engine"}
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
    def _task_from_plan(cls, raw):
        if not isinstance(raw, dict): raise TypeError("Task must be a dictionary.")
        task_id, action = raw.get("id"), raw.get("action")
        title, description = raw.get("title", task_id), raw.get("description", "")
        requires_permission = raw.get("requires_permission", True)
        if not isinstance(task_id, str) or not task_id.strip(): raise ValueError("Task ID must be a non-empty string.")
        if not isinstance(action, str) or not action.strip(): raise ValueError("Task action must be a non-empty string.")
        if not isinstance(title, str): raise TypeError("Task title must be a string.")
        if not isinstance(description, str): raise TypeError("Task description must be a string.")
        if len(title) > cls.MAX_TASK_TEXT_CHARS: raise ValueError("Task title exceeds 2000 characters.")
        if len(description) > cls.MAX_TASK_TEXT_CHARS: raise ValueError("Task description exceeds 2000 characters.")
        if type(requires_permission) is not bool: raise TypeError("Task requires_permission must be a boolean.")
        return Task(id=task_id, name=title, description=description, command=action, requires_permission=requires_permission)

    @staticmethod
    def _evidence(output):
        return output.to_dict() if isinstance(output, CapabilityResult) else None

    @classmethod
    def _validate_plan(cls, plan):
        if not isinstance(plan, dict): return "Plan must be a dictionary."
        if plan.get("status") != "READY": return "Plan is not READY."
        plan_id = plan.get("plan_id")
        if not isinstance(plan_id, str) or not plan_id.strip(): return "Plan must include a non-empty plan_id."
        if len(plan_id) > cls.MAX_PLAN_ID_CHARS: return "Plan ID exceeds 200 characters."
        goal = plan.get("goal", "")
        if not isinstance(goal, str): return "Plan goal must be a string."
        if len(goal) > cls.MAX_GOAL_CHARS: return "Plan goal exceeds 2000 characters."
        tasks = plan.get("tasks")
        if not isinstance(tasks, list) or not tasks: return "Plan must include at least one task."
        if len(tasks) > cls.MAX_TASKS: return "Plan cannot contain more than 100 tasks."
        seen = set()
        for index, raw in enumerate(tasks, 1):
            if not isinstance(raw, dict): return f"Task {index} must be a dictionary."
            task_id, action = raw.get("id"), raw.get("action")
            if not isinstance(task_id, str) or not task_id.strip(): return f"Task {index} is missing required field(s): id."
            if not isinstance(action, str) or not action.strip(): return f"Task {index} is missing required field(s): action."
            if task_id in seen: return f"Duplicate task id: {task_id}"
            seen.add(task_id)
            title, description, permission = raw.get("title", task_id), raw.get("description", ""), raw.get("requires_permission", True)
            if not isinstance(title, str): return f"Task {index} title must be a string."
            if not isinstance(description, str): return f"Task {index} description must be a string."
            if len(title) > cls.MAX_TASK_TEXT_CHARS: return f"Task {index} title exceeds 2000 characters."
            if len(description) > cls.MAX_TASK_TEXT_CHARS: return f"Task {index} description exceeds 2000 characters."
            if type(permission) is not bool: return f"Task {index} requires_permission must be a boolean."
        return None

    @classmethod
    def _validate_request_id(cls, request_id):
        if request_id is None: return None
        if not isinstance(request_id, str): raise TypeError("request_id must be a string or None")
        value = request_id.strip()
        if not value: raise ValueError("request_id must be non-empty when provided")
        if len(value) > cls.MAX_REQUEST_ID_CHARS: raise ValueError("request_id exceeds 200 characters")
        return value

    def _verify_output(self, capability, output, verifier, task, *, injected_executor):
        if verifier is not None: return bool(verifier(task, output))
        if injected_executor and isinstance(output, dict): return bool(output.get("ok", False))
        return self.capability_executor.verify(capability, output)

    def _audit(self, task, capability, status, verified, output=None, error=None, request_id=None):
        self.audit.record(AuditRecord(task.id, task.command, capability, status, verified, error, self._evidence(output), request_id))

    def _result(self, *, status, plan_id, goal, tasks, completed_tasks, failed_task_id, error, capability_results, request_id=None):
        return {"status": status, "plan_id": plan_id, "goal": goal, "request_id": request_id, "completed_tasks": completed_tasks, "failed_task_id": failed_task_id, "error": error, "current_task": next((task.id for task in tasks if task.status.value == "running"), None), "task_results": [task.to_dict() for task in tasks], "capability_results": capability_results, "audit": self.audit.as_dicts()}

    def execute_plan(self, plan, *, executor=None, verifier=None, approved=False, request_id=None):
        self.audit.clear()
        try: request_id = self._validate_request_id(request_id)
        except (TypeError, ValueError) as exc: return self._result(status="failed", plan_id=None, goal="", tasks=[], completed_tasks=0, failed_task_id=None, error=str(exc), capability_results=[], request_id=request_id)
        if executor is not None and not callable(executor): return self._result(status="failed", plan_id=None, goal="", tasks=[], completed_tasks=0, failed_task_id=None, error="Executor must be callable.", capability_results=[], request_id=request_id)
        if verifier is not None and not callable(verifier): return self._result(status="failed", plan_id=None, goal="", tasks=[], completed_tasks=0, failed_task_id=None, error="Verifier must be callable.", capability_results=[], request_id=request_id)
        if type(approved) is not bool: return self._result(status="failed", plan_id=None, goal="", tasks=[], completed_tasks=0, failed_task_id=None, error="approved must be a boolean.", capability_results=[], request_id=request_id)
        validation_error = self._validate_plan(plan)
        if validation_error:
            return self._result(status="failed", plan_id=plan.get("plan_id") if isinstance(plan, dict) else None, goal=plan.get("goal", "") if isinstance(plan, dict) else "", tasks=[], completed_tasks=0, failed_task_id=None, error=validation_error, capability_results=[], request_id=request_id)
        tasks = [self._task_from_plan(raw) for raw in plan["tasks"]]
        capability_results, completed_tasks = [], 0
        for task in tasks:
            route = self.route(task)
            if not route.accepted:
                task.reject(route.reason); self._audit(task, route.capability, "rejected", False, error=route.reason, request_id=request_id)
                return self._result(status="rejected", plan_id=plan["plan_id"], goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=route.reason, capability_results=capability_results, request_id=request_id)
            if task.requires_permission and not approved:
                error = "Permission not approved."; task.reject(error); self._audit(task, route.capability, "rejected", False, error=error, request_id=request_id)
                return self._result(status="rejected", plan_id=plan["plan_id"], goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=error, capability_results=capability_results, request_id=request_id)
            try:
                task.start(); output = executor(task) if executor is not None else self.capability_executor.execute(route.capability, task)
                evidence = self._evidence(output)
                if evidence is not None: capability_results.append(evidence)
                verified = self._verify_output(route.capability, output, verifier, task, injected_executor=executor is not None)
                if not verified:
                    error = "Task verification failed."; task.fail(error); self._audit(task, route.capability, "failed", False, output, error, request_id)
                    return self._result(status="failed", plan_id=plan["plan_id"], goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=error, capability_results=capability_results, request_id=request_id)
                task.complete(output); self._audit(task, route.capability, "completed", True, output, request_id=request_id); completed_tasks += 1
            except Exception as exc:
                task.fail(str(exc)); self._audit(task, route.capability, "failed", False, error=str(exc), request_id=request_id)
                return self._result(status="failed", plan_id=plan["plan_id"], goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=task.id, error=str(exc), capability_results=capability_results, request_id=request_id)
        return self._result(status="completed", plan_id=plan["plan_id"], goal=plan.get("goal", ""), tasks=tasks, completed_tasks=completed_tasks, failed_task_id=None, error=None, capability_results=capability_results, request_id=request_id)
