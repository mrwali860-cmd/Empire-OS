"""
Empire OS
Task Orchestrator — v0.1

Purpose:
Decide which capability should handle a task.

Flow:

Task
  ↓
Classify
  ↓
Route
  ↓
Task Engine
  ↓
Execute
  ↓
Verify
"""

from __future__ import annotations

from dataclasses import dataclass

from .tasks import Task


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
    Deterministic task router for Empire OS.

    v0.1 does not execute tasks itself.
    It only decides which capability should handle them.

    This separation is intentional:

        Orchestrator = Decide
        Task Engine  = Execute
        Agent        = Capability
    """

    def __init__(self) -> None:

        self.routes: dict[str, str] = {
            "inspect_project": "project_inspection",
            "run_tests": "test_runner",
        }

    # -------------------------------------------------
    # Classify
    # -------------------------------------------------

    def classify(self, task: Task) -> str:
        """Return the task command."""

        return task.command

    # -------------------------------------------------
    # Route
    # -------------------------------------------------

    def route(self, task: Task) -> RouteDecision:
        """
        Decide which capability should handle the task.
        """

        command = self.classify(task)

        capability = self.routes.get(command)

        if capability is None:

            return RouteDecision(
                task_id=task.id,
                command=command,
                capability="",
                accepted=False,
                reason=(
                    f"No capability registered "
                    f"for command: {command}"
                ),
            )

        return RouteDecision(
            task_id=task.id,
            command=command,
            capability=capability,
            accepted=True,
            reason="Route accepted.",
        )