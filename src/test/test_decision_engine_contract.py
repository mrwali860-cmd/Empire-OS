"""Contract tests for the safe read-only decision_engine capability."""

import json
import math

from src.agent.capabilities import CapabilityResult, EmpireCapabilityExecutor
from src.agent.decision_engine import DecisionEngineCapability
from src.agent.tasks import Task


def option(option_id="OP1", title="Launch Product", **overrides):
    value = {
        "id": option_id,
        "title": title,
        "description": "Launch a product",
        "roi": 90.0,
        "risk": 20.0,
        "alignment": 95.0,
        "impact": 88.0,
        "execution_time": 25.0,
        "cost": 20.0,
    }
    value.update(overrides)
    return value


def payload(options=None, context=None):
    return {
        "raw_context": context or {"goal": "Increase Revenue", "available_budget": 5000, "available_team": 6},
        "options": options or [option(), option("OP2", "Facebook Ads", roi=80.0)],
    }


def task(value):
    return Task("DEC-1", "Decision", json.dumps(value), "decision_engine", False)


def test_valid_payload_is_accepted():
    assert DecisionEngineCapability.validate_payload(payload())


def test_input_requires_dict_context_and_nonempty_options():
    assert not DecisionEngineCapability.validate_payload({"raw_context": [], "options": [option()]})
    assert not DecisionEngineCapability.validate_payload({"raw_context": {}, "options": []})
    assert not DecisionEngineCapability.validate_payload({"raw_context": {}, "options": [option()] * 101})


def test_option_contract_rejects_bad_text_and_nonfinite_numbers():
    assert not DecisionEngineCapability.validate_payload(payload([option(title="x" * 2001)]))
    assert not DecisionEngineCapability.validate_payload(payload([option(roi=float("nan"))]))
    assert not DecisionEngineCapability.validate_payload(payload([option(risk=float("inf"))]))
    assert not DecisionEngineCapability.validate_payload(payload([option(cost=True)]))


def test_context_size_limit_is_enforced():
    huge = {"goal": "x" * 100_001}
    assert not DecisionEngineCapability.validate_payload(payload(context=huge))


def test_task_validation_requires_json_contract():
    assert DecisionEngineCapability.validate_task(task(payload()))
    assert not DecisionEngineCapability.validate_task(Task("x", "x", "not-json", "decision_engine", False))


def test_execute_returns_normalized_recommendation_and_alternatives():
    result = DecisionEngineCapability().execute(task(payload()))
    assert result.ok
    assert result.error is None
    assert result.capability == "decision_engine"
    assert isinstance(result.data["context"], dict)
    assert result.data["recommended"]["option"]["id"] in {"OP1", "OP2"}
    assert isinstance(result.data["alternatives"], list)
    assert result.data["recommended"]["confidence"] >= 0


def test_execute_rejects_invalid_input_without_traceback():
    result = DecisionEngineCapability().execute(Task("x", "x", "{}", "decision_engine", False))
    assert not result.ok
    assert result.data == {}
    assert result.error == "Invalid decision_engine input contract."
    assert "Traceback" not in result.error


def test_execution_is_deterministic_for_same_input():
    engine = DecisionEngineCapability()
    first = engine.execute(task(payload())).to_dict()
    second = engine.execute(task(payload())).to_dict()
    first["data"]["context"].pop("created_at", None)
    second["data"]["context"].pop("created_at", None)
    assert first == second


def test_verifier_accepts_valid_result():
    executor = EmpireCapabilityExecutor()
    result = DecisionEngineCapability().execute(task(payload()))
    assert executor.verify("decision_engine", result)


def test_verifier_rejects_wrong_capability_and_failed_result():
    executor = EmpireCapabilityExecutor()
    assert not executor.verify("decision_engine", CapabilityResult(True, "other", {}, None))
    assert not executor.verify("decision_engine", CapabilityResult(False, "decision_engine", {}, "failed"))


def test_verifier_rejects_invalid_confidence_and_nonfinite_score():
    executor = EmpireCapabilityExecutor()
    result = DecisionEngineCapability().execute(task(payload()))
    bad = result.data["recommended"]
    bad["confidence"] = 1.1
    assert not executor.verify("decision_engine", result)
    bad["confidence"] = 0.5
    bad["score"]["final_score"] = math.inf
    assert not executor.verify("decision_engine", result)


def test_verifier_rejects_malformed_recommendation():
    executor = EmpireCapabilityExecutor()
    result = DecisionEngineCapability().execute(task(payload()))
    result.data["recommended"] = {}
    assert not executor.verify("decision_engine", result)


def test_decision_capability_does_not_expose_execution_method():
    assert not hasattr(DecisionEngineCapability(), "execute_decision")
    assert not hasattr(DecisionEngineCapability(), "save")
    assert not hasattr(DecisionEngineCapability(), "learn")
