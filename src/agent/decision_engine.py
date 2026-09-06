"""Safe orchestrator adapter for the read-only Decision Engine."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from typing import Any

from src.business.decision.decision_engine import DecisionEngine
from src.business.decision.models import DecisionOption

from .capabilities import CapabilityResult
from .tasks import Task


class DecisionEngineCapability:
    """Validate, execute, and normalize the read-only decision contract."""

    MAX_OPTIONS = 100
    MAX_CONTEXT_BYTES = 100_000
    MAX_TEXT_LENGTH = 2_000

    _OPTION_NUMERIC_FIELDS = ("roi", "risk", "alignment", "impact", "execution_time", "cost")
    _OPTION_TEXT_FIELDS = ("id", "title", "description")

    def __init__(self) -> None:
        self.engine = DecisionEngine()

    @classmethod
    def parse_task(cls, task: Any) -> dict[str, Any] | None:
        if not isinstance(task, Task) or not isinstance(task.description, str):
            return None
        try:
            payload = json.loads(task.description)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    @classmethod
    def validate_payload(cls, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        context, options = payload.get("raw_context"), payload.get("options")
        if not isinstance(context, dict) or not isinstance(options, list) or not (1 <= len(options) <= cls.MAX_OPTIONS):
            return False
        try:
            if len(json.dumps(context, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")) > cls.MAX_CONTEXT_BYTES:
                return False
        except (TypeError, ValueError):
            return False
        return all(cls._valid_option(option) for option in options)

    @classmethod
    def _valid_option(cls, option: Any) -> bool:
        if isinstance(option, DecisionOption):
            option = asdict(option)
        if not isinstance(option, dict):
            return False
        for field in cls._OPTION_TEXT_FIELDS:
            value = option.get(field)
            if not isinstance(value, str) or not value or len(value) > cls.MAX_TEXT_LENGTH:
                return False
        for field in cls._OPTION_NUMERIC_FIELDS:
            value = option.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                return False
        return True

    @classmethod
    def validate_task(cls, task: Any) -> bool:
        return cls.validate_payload(cls.parse_task(task))

    @staticmethod
    def _option(option: dict[str, Any]) -> DecisionOption:
        return DecisionOption(id=option["id"], title=option["title"], description=option["description"], roi=option["roi"], risk=option["risk"], alignment=option["alignment"], impact=option["impact"], execution_time=option["execution_time"], cost=option["cost"])

    @staticmethod
    def _result_dict(result: Any) -> dict[str, Any]:
        value = asdict(result)
        value["confidence"] = max(0.0, min(1.0, float(result.confidence) / 100.0))
        return value

    def execute(self, task: Task) -> CapabilityResult:
        payload = self.parse_task(task)
        if not self.validate_payload(payload):
            return CapabilityResult(False, "decision_engine", {}, "Invalid decision_engine input contract.")
        try:
            context = self.engine.context.understand(payload["raw_context"])
            evaluated = []
            for raw_option in payload["options"]:
                option = self._option(raw_option)
                result = self.engine.evaluator.evaluate(option=option, roi=option.roi, risk=option.risk, alignment=option.alignment, impact=option.impact, execution_time=option.execution_time, cost=option.cost)
                result.reasons = self.engine.explainer.explain(result)
                evaluated.append(result)
            ranked = self.engine.ranking.rank(evaluated)
            recommended = self.engine.recommender.recommend(ranked)
            alternatives = self.engine.recommender.alternatives(ranked)
            data = {"context": asdict(context), "recommended": self._result_dict(recommended), "alternatives": [self._result_dict(item) for item in alternatives]}
            return CapabilityResult(True, "decision_engine", data, None)
        except Exception:
            return CapabilityResult(False, "decision_engine", {}, "Decision engine evaluation failed.")
