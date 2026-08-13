"""
Empire OS
Goal Engine — v0.2

Purpose:
Convert founder goals into deterministic executable tasks
and optionally queue them in the Task Engine.

Flow:

Founder Goal
    ↓
Goal Engine
    ↓
Task Plan
    ↓
Task Engine
    ↓
Execution
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .task_engine import TaskEngine
from .tasks import Task


@dataclass(frozen=True, slots=True)
class FounderGoal:
    """A high-level objective provided by the founder."""

    id: str
    title: str
    description: str


class GoalEngine:
    """
    Convert founder goals into executable Empire OS tasks.

    v0.2 adds TaskEngine integration.

    The GoalEngine plans.
    The TaskEngine queues and manages execution.
    """

    def __init__(self, task_engine: TaskEngine) -> None:
        self.task_engine = task_engine
        self.goals: dict[str, FounderGoal] = {}

    # -------------------------------------------------
    # Create Goal
    # -------------------------------------------------

    def create_goal(
        self,
        title: str,
        description: str,
    ) -> FounderGoal:
        """Create and store a founder goal."""

        if not title.strip():
            raise ValueError("Goal title cannot be empty.")

        if not description.strip():
            raise ValueError(
                "Goal description cannot be empty."
            )

        goal = FounderGoal(
            id=f"goal-{uuid4().hex[:8]}",
            title=title.strip(),
            description=description.strip(),
        )

        self.goals[goal.id] = goal

        return goal

    # -------------------------------------------------
    # Get Goal
    # -------------------------------------------------

    def get_goal(
        self,
        goal_id: str,
    ) -> FounderGoal | None:
        """Return a stored goal."""

        return self.goals.get(goal_id)

    # -------------------------------------------------
    # Plan Goal
    # -------------------------------------------------

    def plan_goal(
        self,
        goal: FounderGoal,
    ) -> list[Task]:
        """
        Convert a founder goal into deterministic tasks.

        v0.2 plan:

        1. Inspect project
        2. Run tests
        """

        return [
            Task(
                id=f"{goal.id}-inspect",
                name="Inspect Project",
                description=(
                    f"Inspect project for goal: "
                    f"{goal.title}"
                ),
                command="inspect_project",
                requires_permission=True,
            ),
            Task(
                id=f"{goal.id}-tests",
                name="Run Tests",
                description=(
                    f"Run tests for goal: "
                    f"{goal.title}"
                ),
                command="run_tests",
                requires_permission=False,
            ),
        ]

    # -------------------------------------------------
    # Queue Goal
    # -------------------------------------------------

    def queue_goal(
        self,
        goal: FounderGoal,
    ) -> list[Task]:
        """
        Plan a goal and add all generated tasks
        to the TaskEngine queue.
        """

        tasks = self.plan_goal(goal)

        queued: list[Task] = []

        for task in tasks:
            queued.append(
                self.task_engine.add_task(task)
            )

        return queued

    # -------------------------------------------------
    # Create + Queue
    # -------------------------------------------------

    def create_and_queue(
        self,
        title: str,
        description: str,
    ) -> tuple[FounderGoal, list[Task]]:
        """
        Create a founder goal and immediately
        convert it into queued tasks.
        """

        goal = self.create_goal(
            title=title,
            description=description,
        )

        tasks = self.queue_goal(goal)

        return goal, tasks