"""Tests for LLM-backed Brain reasoning and intent detection."""

from src.agent.capabilities import EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator
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
        if self.error: raise self.error
        return self.output

    def classify_intent(self, user_input):
        self.intent_calls += 1
        if self.intent_error: raise self.intent_error
        return self.intent_output


def test_pipeline_uses_valid_llm_reasoning():
    llm = FakeLLM(output={"goal": "Acquire the first client", "assumptions": ["Business type is AGENCY"], "constraints": ["Limited budget"], "next_actions": ["Define offer", "Contact qualified prospects"], "confidence": 0.91}, intent_output={"intent": "CLIENT_ACQUISITION", "confidence": 0.96})
    result = BrainPipeline(llm=llm).process("I need my first client for my agency")
    assert llm.calls == 1 and llm.intent_calls == 1
    assert "Goal: Acquire the first client" in result and "Define offer" in result


def test_pipeline_falls_back_when_llm_fails():
    llm = FakeLLM(error=LLMProviderError("provider unavailable"), intent_error=LLMProviderError("provider unavailable"))
    result = BrainPipeline(llm=llm).process("I need my first client for my agency")
    assert "Goal: I need my first client for my agency" in result
    assert "Status: READY FOR EXECUTION" in result


def test_pipeline_falls_back_when_llm_output_is_invalid():
    llm = FakeLLM(output={"goal": "Broken result", "assumptions": [], "constraints": [], "next_actions": [], "confidence": 0.9}, intent_output={"intent": "SYSTEM_BUILDING", "confidence": 0.9})
    result = BrainPipeline(llm=llm).process("Build my system")
    assert "Goal: Build my system" in result
    assert "Clarify the objective and success criteria" in result


def test_pipeline_falls_back_when_llm_returns_bad_confidence():
    llm = FakeLLM(output={"goal": "Build the system", "assumptions": [], "constraints": [], "next_actions": ["Start with the smallest testable step"], "confidence": 4.0}, intent_output={"intent": "SYSTEM_BUILDING", "confidence": 0.9})
    result = BrainPipeline(llm=llm).process("Build my system")
    assert "Start with the smallest testable step" not in result


def test_llm_intent_is_used_when_valid():
    llm = FakeLLM(intent_output={"intent": "REVENUE_GROWTH", "confidence": 0.93})
    assert BrainPipeline(llm=llm).intent.detect("How do I grow this business?") == "REVENUE_GROWTH"


def test_invalid_llm_intent_uses_keyword_fallback():
    llm = FakeLLM(intent_output={"intent": "MADE_UP_INTENT", "confidence": 0.99})
    assert BrainPipeline(llm=llm).intent.detect("I need a new client") == "CLIENT_ACQUISITION"


def test_failed_llm_intent_uses_keyword_fallback():
    llm = FakeLLM(intent_error=LLMProviderError("provider unavailable"))
    assert BrainPipeline(llm=llm).intent.detect("I need to hire a developer") == "HIRING"


def test_repository_status_uses_deterministic_brain_route():
    result = BrainPipeline(llm=FakeLLM(intent_output={"intent": "UNKNOWN", "confidence": 0.99})).process("Check my repository status")
    assert "Goal: Check my repository status" in result and "Check Git status" in result and "git_status" in result


def test_repository_status_executes_through_brain_to_orchestrator():
    pipeline = BrainPipeline(llm=FakeLLM(intent_output={"intent": "UNKNOWN", "confidence": 0.99}))
    result = pipeline.process("Check my repository status", execute=True)
    assert "Execution Status: COMPLETED" in result and "GIT_STATUS → PASS" in result
    assert "Audit Records: 1" in result and "VERIFIED" in result


def test_project_search_routes_and_executes_through_brain(tmp_path):
    (tmp_path / "app.py").write_text("TARGET_VALUE = 42\n", encoding="utf-8")
    pipeline = BrainPipeline(llm=FakeLLM(intent_output={"intent": "UNKNOWN", "confidence": 0.99}), orchestrator=EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)))
    result = pipeline.process("Search project for TARGET_VALUE", execute=True)
    assert "Execution Status: COMPLETED" in result and "PROJECT_SEARCH → PASS" in result and "TARGET_VALUE" in result


def test_file_write_requires_approval_through_brain(tmp_path):
    pipeline = BrainPipeline(llm=FakeLLM(intent_output={"intent": "UNKNOWN", "confidence": 0.99}), orchestrator=EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)))
    result = pipeline.process("Write file: app.py content: VALUE = 42\n", execute=True, approved=False)
    assert "Execution Status: REJECTED" in result
    assert not (tmp_path / "app.py").exists()


def test_file_write_executes_after_approval_through_brain(tmp_path):
    pipeline = BrainPipeline(llm=FakeLLM(intent_output={"intent": "UNKNOWN", "confidence": 0.99}), orchestrator=EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)))
    result = pipeline.process("Write file: app.py content: VALUE = 42\n", execute=True, approved=True)
    assert "Execution Status: COMPLETED" in result
    assert "FILE_WRITE → PASS" in result
    assert "Bytes Written:" in result
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "VALUE = 42\n"
