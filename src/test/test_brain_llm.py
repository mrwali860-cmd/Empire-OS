"""Tests for LLM-backed Brain reasoning and deterministic fallback."""

from src.brain.pipeline import BrainPipeline


class FakeLLM:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = 0

    def reason(self, payload):
        self.calls += 1
        if self.error:
            raise self.error
        return self.output


def test_pipeline_uses_valid_llm_reasoning():
    llm = FakeLLM(
        output={
            "goal": "Acquire the first client",
            "assumptions": ["Business type is AGENCY"],
            "constraints": ["Limited budget"],
            "next_actions": ["Define offer", "Contact qualified prospects"],
            "confidence": 0.91,
        }
    )

    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("I need my first client for my agency")

    assert llm.calls == 1
    assert "Acquire the first client" in result
    assert "Define offer" in result


def test_pipeline_falls_back_when_llm_fails():
    llm = FakeLLM(error=RuntimeError("provider unavailable"))

    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("I need my first client for my agency")

    assert llm.calls == 1
    assert "Goal: I need my first client for my agency" in result
    assert "Status: READY FOR EXECUTION" in result


def test_pipeline_falls_back_when_llm_output_is_invalid():
    llm = FakeLLM(
        output={
            "goal": "Broken result",
            "assumptions": [],
            "constraints": [],
            "next_actions": [],
            "confidence": 0.9,
        }
    )

    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("Build my system")

    assert llm.calls == 1
    assert "Goal: Build my system" in result
    assert "Clarify the objective and success criteria" in result


def test_pipeline_falls_back_when_llm_returns_bad_confidence():
    llm = FakeLLM(
        output={
            "goal": "Build the system",
            "assumptions": [],
            "constraints": [],
            "next_actions": ["Start with the smallest testable step"],
            "confidence": 4.0,
        }
    )

    pipeline = BrainPipeline(llm=llm)
    result = pipeline.process("Build my system")

    assert "Goal: Build my system" in result
    assert "Start with the smallest testable step" not in result
