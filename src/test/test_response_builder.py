from src.brain.response import ResponseBuilder


def test_response_renders_capability_evidence():
    plan = {
        "status": "READY",
        "plan_id": "PLAN-001",
        "goal": "Inspect project",
        "tasks": [],
    }
    result = {
        "status": "completed",
        "completed_tasks": 1,
        "failed_task_id": None,
        "error": None,
        "capability_results": [
            {
                "ok": True,
                "capability": "project_inspection",
                "data": {"files": 3, "directories": 2},
                "error": None,
            }
        ],
    }

    response = ResponseBuilder().build(plan, {}, orchestration_result=result)

    assert "Execution Status: COMPLETED" in response
    assert "Capability Results: 1" in response
    assert "PROJECT_INSPECTION → PASS" in response


def test_response_omits_empty_capability_evidence():
    plan = {"status": "READY", "plan_id": "PLAN-002", "goal": "Run tests", "tasks": []}
    result = {"status": "failed", "completed_tasks": 0, "failed_task_id": "TASK-001", "error": "Task verification failed.", "capability_results": []}

    response = ResponseBuilder().build(plan, {}, orchestration_result=result)

    assert "Execution Status: FAILED" in response
    assert "Capability Results:" not in response
