import pytest

from src.brain.pipeline import BrainPipeline


class StubPipeline:
    def __init__(self, response="READY"):
        self.response = response

    def process(self, user_input, **kwargs):
        return self.response


def test_pipeline_rejects_non_string_user_input():
    pipeline = BrainPipeline.__new__(BrainPipeline)
    with pytest.raises(TypeError, match="User input must be a string"):
        pipeline.process(123)


def test_pipeline_rejects_empty_user_input():
    pipeline = BrainPipeline.__new__(BrainPipeline)
    with pytest.raises(ValueError, match="User input must not be empty"):
        pipeline.process("   ")


# CI trigger marker: contract tests unchanged.
