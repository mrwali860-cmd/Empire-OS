from src.brain.pipeline import BrainPipeline


class StubIntent:
    def detect(self, user_input):
        return "execution"


class StubContext:
    def analyze(self, user_input):
        return {"user_input": user_input}


class StubThinking:
    def think(self, intent, context):
        return "Execution strategy"


class StubReasoning:
    def as_dict(self):
        return {
            "goal": "Run project tests",
            "assumptions": (),
            "constraints": (),
            "next_actions": ("Run tests",),
            "confidence": 1.0,
        }

    def summary(self):
        return "Goal: Run project tests\n1. Run tests"


class StubVerifier:
    def verify(self, result):
        return {"verified": True, "reason": "ok"}


class StubDecision:
    def decide(self, summary):
        return {"status": "APPROVED", "decision": summary}


class StubPlanner:
    def plan(self, decision):
        return {
            "status": "READY",
            "plan_id": "PLAN-INTEGRATION",
            "goal": "Run project tests",
            "tasks": [
                {
                    "id": "PLAN-INTEGRATION-T01",
                    "title": "Run tests",
                    "description": "Execute planned step: Run tests",
                    "action": "run_tests",
                    "requires_permission": False,
                    "verification": "Verify the outcome.",
                    "status": "PENDING",
                }
            ],
            "verification_required": True,
        }


class StubOrchestrator:
    def __init__(self):
        self.received_plan = None

    def execute_plan(self, plan, *, executor, verifier=None, approved=False):
        self.received_plan = plan
        return {
            "status": "completed",
            "plan_id": plan["plan_id"],
            "goal": plan["goal"],
            "completed_tasks": 1,
            "failed_task_id": None,
            "error": None,
        }


class StubLLM:
    def reason(self, payload):
        return {
            "goal": "Run project tests",
            "assumptions": [],
            "constraints": [],
            "next_actions": ["Run tests"],
            "confidence": 1.0,
        }


def test_pipeline_sends_plan_to_orchestrator_when_execution_enabled():
    orchestrator = StubOrchestrator()
    pipeline = BrainPipeline(llm=StubLLM(), intent_llm=StubLLM(), orchestrator=orchestrator)
    pipeline.intent = StubIntent()
    pipeline.context = StubContext()
    pipeline.thinking = StubThinking()
    pipeline.verifier = StubVerifier()
    pipeline.decision = StubDecision()
    pipeline.planner = StubPlanner()

    result = pipeline.process(
        "run the project tests",
        execute=True,
        approved=True,
        executor=lambda task: {"ok": True},
    )

    assert orchestrator.received_plan["goal"] == "Run project tests"
    assert "Execution Status: COMPLETED" in result
    assert "Completed Tasks: 1" in result


def test_pipeline_does_not_execute_by_default():
    orchestrator = StubOrchestrator()
    pipeline = BrainPipeline(llm=StubLLM(), intent_llm=StubLLM(), orchestrator=orchestrator)
    pipeline.intent = StubIntent()
    pipeline.context = StubContext()
    pipeline.thinking = StubThinking()
    pipeline.verifier = StubVerifier()
    pipeline.decision = StubDecision()
    pipeline.planner = StubPlanner()

    result = pipeline.process("run the project tests")

    assert orchestrator.received_plan is None
    assert "Status: READY FOR EXECUTION" in result
