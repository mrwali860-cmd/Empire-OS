from src.agent.agent import EmpireAgent
from src.agent.tasks import TaskStatus


class RecordingOrchestrator:
    def __init__(self):
        self.calls = []

    def execute_plan(self, plan, *, approved=False):
        self.calls.append((plan, approved))
        return {
            "status": "completed",
            "plan_id": "agent-task-plan",
            "goal": plan["goal"],
            "completed_tasks": 1,
            "failed_task_id": None,
            "error": None,
            "task_results": [
                {
                    "id": plan["tasks"][0]["id"],
                    "status": "completed",
                    "result": {"ok": True},
                    "error": None,
                }
            ],
            "capability_results": [],
            "audit": [],
        }


def test_agent_task_processing_delegates_execution_to_orchestrator():
    orchestrator = RecordingOrchestrator()
    agent = EmpireAgent(".", orchestrator=orchestrator)
    task = agent.create_task(
        task_id="integration-task",
        name="Integration task",
        description="Verify canonical execution boundary.",
        command="run_tests",
        requires_permission=False,
    )

    processed = agent.process_next_task()

    assert len(orchestrator.calls) == 1
    plan, approved = orchestrator.calls[0]
    assert approved is False
    assert plan["status"] == "READY"
    assert plan["tasks"][0]["id"] == task.id
    assert plan["tasks"][0]["action"] == "run_tests"
    assert processed is task
    assert task.status is TaskStatus.COMPLETED
    assert task.result == {"ok": True}
