from src.brain.pipeline import BrainPipeline
from src.agent.orchestrator import EmpireOrchestrator


class StubIntent:
    def detect(self, user_input): return "execution"
class StubContext:
    def analyze(self, user_input): return {"user_input": user_input}
class StubThinking:
    def think(self, intent, context): return "Execution strategy"
class StubReasoning:
    def as_dict(self): return {"goal": "Run project tests", "assumptions": (), "constraints": (), "next_actions": ("Run tests",), "confidence": 1.0}
    def summary(self): return "Goal: Run project tests\n1. Run tests"
class StubVerifier:
    def verify(self, result): return {"verified": True, "reason": "ok"}
class StubDecision:
    def decide(self, summary): return {"status": "APPROVED", "decision": summary}
class StubPlanner:
    def plan(self, decision):
        return {"status": "READY", "plan_id": "PLAN-INTEGRATION", "goal": "Run project tests", "tasks": [{"id": "PLAN-INTEGRATION-T01", "title": "Run tests", "description": "Execute planned step: Run tests", "action": "run_tests", "requires_permission": False, "verification": "Verify the outcome.", "status": "PENDING"}], "verification_required": True}
class StubOrchestrator:
    def __init__(self): self.received_plan = None; self.received_request_id = None
    def execute_plan(self, plan, *, executor, verifier=None, approved=False, request_id=None):
        self.received_plan = plan; self.received_request_id = request_id
        return {"status": "completed", "plan_id": plan["plan_id"], "goal": plan["goal"], "completed_tasks": 1, "failed_task_id": None, "error": None}
class StubLLM:
    def reason(self, payload): return {"goal": "Run project tests", "assumptions": [], "constraints": [], "next_actions": ["Run tests"], "confidence": 1.0}


def configured_pipeline(orchestrator):
    pipeline = BrainPipeline(llm=StubLLM(), intent_llm=StubLLM(), orchestrator=orchestrator)
    pipeline.intent, pipeline.context, pipeline.thinking = StubIntent(), StubContext(), StubThinking()
    pipeline.verifier, pipeline.decision, pipeline.planner = StubVerifier(), StubDecision(), StubPlanner()
    return pipeline


def test_pipeline_sends_plan_to_orchestrator_when_execution_enabled():
    orchestrator = StubOrchestrator()
    result = configured_pipeline(orchestrator).process("run the project tests", execute=True, approved=True, executor=lambda task: {"ok": True})
    assert orchestrator.received_plan["goal"] == "Run project tests"
    assert orchestrator.received_request_id is None
    assert "Execution Status: COMPLETED" in result
    assert "Completed Tasks: 1" in result


def test_pipeline_does_not_execute_by_default():
    orchestrator = StubOrchestrator()
    result = configured_pipeline(orchestrator).process("run the project tests")
    assert orchestrator.received_plan is None
    assert "Status: READY FOR EXECUTION" in result


def test_business_request_id_reaches_execution_result_and_audit():
    orchestrator = EmpireOrchestrator()
    pipeline = configured_pipeline(orchestrator)
    request_id = "BUSINESS-REQ-001"
    result = pipeline.process("run the project tests", execute=True, approved=True, executor=lambda task: {"ok": True}, request_id=request_id)
    assert "Execution Status: COMPLETED" in result
    assert orchestrator.audit.records[0].request_id == request_id
    assert orchestrator.audit.records[0].to_dict()["request_id"] == request_id
