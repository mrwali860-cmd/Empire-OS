"""
Empire OS
Agent Control Interface — v0.4
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .agent import AgentAction, AgentResult, EmpireAgent


@dataclass(frozen=True, slots=True)
class ControlCommand:
    """A command exposed to an external controller."""

    name: str
    description: str
    requires_permission: bool
    executor: Callable[[], object]


@dataclass(slots=True)
class ControlRequest:
    """A command received by the control interface."""

    command: str
    approved: bool = False


class AgentControl:
    """Safe control boundary for EmpireAgent."""

    def __init__(self, agent: EmpireAgent):
        self.agent = agent

        self.commands: dict[str, ControlCommand] = {
            "inspect_project": ControlCommand(
                name="Project Inspection",
                description=(
                    "Inspect the Empire OS project structure."
                ),
                requires_permission=True,
                executor=self.agent.inspect_project,
            ),
            "run_tests": ControlCommand(
                name="Run Tests",
                description=(
                    "Run the Empire OS test suite."
                ),
                requires_permission=False,
                executor=self.agent.run_tests,
            ),
        }

    def available_commands(
        self,
    ) -> list[dict[str, object]]:
        """Return commands exposed to external controllers."""

        return [
            {
                "command": key,
                "name": command.name,
                "description": command.description,
                "requires_permission": (
                    command.requires_permission
                ),
            }
            for key, command in self.commands.items()
        ]

    def handle(
        self,
        request: ControlRequest,
    ) -> AgentResult:
        """Execute a registered command directly."""

        command = self.commands.get(request.command)

        if command is None:
            return AgentResult(
                action=request.command,
                status="rejected",
                error=(
                    f"Command not allowed: "
                    f"{request.command}"
                ),
            )

        action = AgentAction(
            name=command.name,
            description=command.description,
            requires_permission=(
                command.requires_permission
            ),
            executor=command.executor,
        )

        return self.agent.run_action(
            action,
            approved=request.approved,
        )