"""
Empire OS
Agent API — v0.5
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .agent import EmpireAgent
from .control import AgentControl, ControlRequest
from .tasks import Task


class CommandRequest(BaseModel):
    command: str
    approved: bool = False


class TaskRequest(BaseModel):
    id: str
    name: str
    description: str
    command: str
    requires_permission: bool = True


agent = EmpireAgent(".")
control = AgentControl(agent)

app = FastAPI(
    title="Empire OS Agent API",
    version="0.5",
)


@app.get("/status")
def status() -> dict[str, object]:
    return {
        "system": "Empire OS",
        "agent": "EmpireAgent",
        "status": "online",
    }


@app.get("/commands")
def commands() -> list[dict[str, object]]:
    return control.available_commands()


@app.get("/tasks")
def tasks() -> list[dict[str, object]]:
    return agent.task_engine.to_dict()


@app.get("/tasks/summary")
def task_summary() -> dict[str, int]:
    return agent.task_engine.summary()


@app.post("/tasks")
def create_task(
    request: TaskRequest,
) -> dict[str, object]:
    """Create a task and add it to the queue."""

    task = agent.create_task(
        task_id=request.id,
        name=request.name,
        description=request.description,
        command=request.command,
        requires_permission=request.requires_permission,
    )

    return task.to_dict()


@app.post("/tasks/process")
def process_next_task(
    approved: bool = False,
) -> dict[str, object]:
    """Process the next pending task."""

    task = agent.process_next_task(
        approved=approved,
    )

    if task is None:
        return {
            "status": "idle",
            "message": "No pending tasks.",
        }

    return task.to_dict()


@app.post("/command")
def execute_command(
    request: CommandRequest,
) -> dict[str, object]:
    """Execute a command through the existing control layer."""

    result = control.handle(
        ControlRequest(
            command=request.command,
            approved=request.approved,
        )
    )

    return {
        "action": result.action,
        "status": result.status,
        "output": result.output,
        "error": result.error,
    }