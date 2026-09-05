from src.agent.capabilities import EmpireCapabilityExecutor
from src.agent.orchestrator import EmpireOrchestrator
from src.brain.pipeline import BrainPipeline


class UnknownLLM:
    def classify_intent(self, user_input):
        return {"intent": "UNKNOWN", "confidence": 0.99}

    def reason(self, payload):
        return None


def test_file_read_routes_from_brain_to_orchestrator(tmp_path):
    target = tmp_path / "app.py"
    target.write_text("VALUE = 42\n", encoding="utf-8")
    pipeline = BrainPipeline(
        llm=UnknownLLM(),
        orchestrator=EmpireOrchestrator(EmpireCapabilityExecutor(project_root=tmp_path)),
    )
    result = pipeline.process("Read file app.py", execute=True)
    assert "Execution Status: COMPLETED" in result
    assert "FILE_READ → PASS" in result
    assert "Path: app.py" in result
    assert "VALUE = 42" in result
