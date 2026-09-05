"""Structured execution planning for Empire OS."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PlanTask:
    """A safe, machine-readable unit of planned work."""

    id: str
    title: str
    description: str
    action: str
    requires_permission: bool
    verification: str
    status: str = "PENDING"

    def as_dict(self):
        return asdict(self)


class ExecutionPlanner:
    """Convert an approved decision into a safe execution contract.

    The planner never turns arbitrary model text into shell commands. Known
    capabilities receive explicit action names; everything else is routed to
    manual review until an executor explicitly supports that capability.
    """

    ACTION_RULES = (
        ("inspect", "inspect_project", False),
        ("run tests", "run_tests", False),
        ("test", "run_tests", False),
    )

    @staticmethod
    def _plan_id(decision_text: str) -> str:
        digest = hashlib.sha256(decision_text.encode("utf-8")).hexdigest()[:12]
        return f"PLAN-{digest}"

    @staticmethod
    def _extract_goal(decision_text: str) -> str:
        for line in decision_text.splitlines():
            match = re.match(r"^\s*Goal:\s*(.+?)\s*$", line, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _extract_actions(decision_text: str) -> list[str]:
        actions = []
        for line in decision_text.splitlines():
            match = re.match(r"^\s*\d+[.)]\s*(.+?)\s*$", line)
            if match:
                actions.append(match.group(1))
        if not actions and decision_text.strip():
            actions.append(decision_text.strip())
        return actions

    @classmethod
    def _map_action(cls, title: str):
        normalized = title.lower()
        for keyword, action, permission in cls.ACTION_RULES:
            if keyword in normalized:
                return action, permission
        return "MANUAL_REVIEW", True

    def plan(self, decision):
        if not decision or decision.get("status") != "APPROVED":
            return {
                "status": "FAILED",
                "plan_id": None,
                "goal": "",
                "tasks": [],
                "verification_required": True,
            }

        decision_text = str(decision.get("decision", "")).strip()
        actions = self._extract_actions(decision_text)
        plan_id = self._plan_id(decision_text)
        goal = self._extract_goal(decision_text)
        tasks = []

        for index, title in enumerate(actions, start=1):
            action, permission = self._map_action(title)
            tasks.append(
                PlanTask(
                    id=f"{plan_id}-T{index:02d}",
                    title=title,
                    description=f"Execute planned step: {title}",
                    action=action,
                    requires_permission=permission,
                    verification="Verify the outcome before marking the task complete.",
                ).as_dict()
            )

        return {
            "status": "READY",
            "plan_id": plan_id,
            "goal": goal,
            "tasks": tasks,
            "verification_required": True,
        }
