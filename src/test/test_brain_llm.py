"""Tests for LLM-backed Brain reasoning and intent detection."""

from src.agent.orchestrator import OrchestrationStatus
from src.brain.llm import LLMProviderError
from src.brain.pipeline import BrainPipeline


class FakeLLM:
    def __init__(self, output=None, error=None, intent_output=None, intent_error=None):
        self.output = output
        self.error = error
        self.intent_output = intent_output or {"intent": "UNKNOWN", "confidence": 0.5}
        self.intent_error = intent_error
        self.calls = 0
        self.intent_calls = 0

    def reason(self, payload):
        self.calls += 1
        if self.error:
            raise self.error
        return self.output

    def classify_intent(self, user_input):
        self.intent_calls += 1
        if self.intent_error:
            raise self.intent_error
        return self.intent_output


def test_pipeline_uses_valid_llm_reasoning():
    llm = FakeLLM(
        output={
            "goal": "Acquire the first client",
            "assumptions": ["Business type is AGENCY"],
            "constraints": ["Limited budget"],
            "next_actions": ["Define offer", "Contact qualified prospects"],
            "confidence": 0.91,
        },
        intent_output={"intent": "CLIENT_ACQUISITION", "confidence": 0.96},
    )
    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("I need my first client for my agency")
    assert llm.calls == 1
    assert llm.intent_calls == 1
    assert "Goal: Acquire the first client" in result
    assert "Acquire the first client" in result
    assert "Define offer" in result


def test_pipeline_falls_back_when_llm_fails():
    llm = FakeLLM(error=LLMProviderError("provider unavailable"), intent_error=LLMProviderError("provider unavailable"))
    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("I need my first client for my agency")
    assert llm.calls == 1
    assert llm.intent_calls == 1
    assert "Goal: I need my first client for my agency" in result
    assert "Status: READY FOR EXECUTION" in result


def test_pipeline_falls_back_when_llm_output_is_invalid():
    llm = FakeLLM(
        output={"goal": "Broken result", "assumptions": [], "constraints": [], "next_actions": [], "confidence": 0.9},
        intent_output={"intent": "SYSTEM_BUILDING", "confidence": 0.9},
    )
    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("Build my system")
    assert llm.calls == 1
    assert "Goal: Build my system" in result
    assert "Clarify the objective and success criteria" in result


def test_pipeline_falls_back_when_llm_returns_bad_confidence():
    llm = FakeLLM(
        output={"goal": "Build the system", "assumptions": [], "constraints": [], "next_actions": ["Start with the smallest testable step"], "confidence": 4.0},
        intent_output={"intent": "SYSTEM_BUILDING", "confidence": 0.9},
    )
    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("Build my system")
    assert "Goal: Build my system" in result
    assert "Start with the smallest testable step" not in result


def test_llm_intent_is_used_when_valid():
    llm = FakeLLM(intent_output={"intent": "REVENUE_GROWTH", "confidence": 0.93})
    pipeline = BrainPipeline(llm=llm)
    assert pipeline.intent.detect("How do I grow this business?") == "REVENUE_GROWTH"
    assert llm.intent_calls == 1


def test_invalid_llm_intent_uses_keyword_fallback():
    llm = FakeLLM(intent_output={"intent": "MADE_UP_INTENT", "confidence": 0.99})
    pipeline = BrainPipeline(llm=llm)
    assert pipeline.intent.detect("I need a new client") == "CLIENT_ACQUISITION"


def test_failed_llm_intent_uses_keyword_fallback():
    llm = FakeLLM(intent_error=LLMProviderError("provider unavailable"))
    pipeline = BrainPipeline(llm=llm)
    assert pipeline.intent.detect("I need to hire a developer") == "HIRING"


def test_repository_status_uses_deterministic_brain_route():
    llm = FakeLLM(intent_output={"intent": "UNKNOWN", "confidence": 0.99})
    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("Check my repository status")
    assert "Goal: Check my repository status" in result
    assert "Check Git status" in result
    assert "git_status" in result


def test_repository_status_executes_through_brain_to_orchestrator():
    llm = FakeLLM(intent_output={"intent": "UNKNOWN", "confidence": 0.99})
    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("Check my repository status", execute=True)
    assert "Execution Status: COMPLETED" in result
    assert "GIT_STATUS → PASS" in result
    assert "Branch:" in result
    assert "Commit SHA:" in result
    assert "Audit Records: 1" in result
    assert "VERIFIED" in result
    assert pipeline.orchestrator.audit.records[0].status == "completed"
    assert pipeline.orchestrator.audit.records[0].verified is True
