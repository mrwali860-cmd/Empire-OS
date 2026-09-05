"""Deterministic reasoning layer for Empire Brain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    """Structured result of a reasoning pass."""

    goal: str
    assumptions: tuple[str, ...]
    constraints: tuple[str, ...]
    next_actions: tuple[str, ...]
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "assumptions": list(self.assumptions),
            "constraints": list(self.constraints),
            "next_actions": list(self.next_actions),
            "confidence": self.confidence,
        }

    def summary(self) -> str:
        actions = "\n".join(
            f"{index}. {action}"
            for index, action in enumerate(self.next_actions, start=1)
        )
        return (
            f"Goal: {self.goal}\n"
            f"Assumptions: {', '.join(self.assumptions) or 'None'}\n"
            f"Constraints: {', '.join(self.constraints) or 'None'}\n"
            f"Confidence: {self.confidence:.2f}\n"
            f"Next actions:\n{actions}"
        )


class ReasoningEngine:
    """Turn intent/context/thinking into an explicit, testable plan."""

    @staticmethod
    def _project_search_query(text: str) -> str:
        normalized = text.strip()
        prefixes = (
            "search project for ",
            "search code for ",
            "search repository for ",
            "find in project ",
            "find in code ",
            "find code ",
        )
        lowered = normalized.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return normalized[len(prefix):].strip()
        return normalized

    @staticmethod
    def _file_path(text: str) -> str:
        normalized = text.strip()
        prefixes = ("read file ", "open file ", "show file ", "view file ", "display file ")
        lowered = normalized.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                return normalized[len(prefix):].strip()
        return normalized

    def reason(self, user_input: str, intent: str, context: dict[str, Any], thinking_result: str) -> ReasoningResult:
        text = user_input.strip()
        assumptions: list[str] = []
        constraints: list[str] = []
        if context.get("experience") != "UNKNOWN":
            assumptions.append(f"Experience level is {context['experience']}")
        if context.get("business") != "UNKNOWN":
            assumptions.append(f"Business type is {context['business']}")
        if context.get("urgency") == "HIGH":
            constraints.append("High urgency")
        if context.get("budget") != "UNKNOWN":
            constraints.append(f"Budget: {context['budget']}")
        goal = text or "Clarify the user's objective"
        actions = tuple(
            line.strip()[3:]
            for line in thinking_result.splitlines()
            if line.strip()[:2].isdigit() and line.strip()[2:3] == "."
        )
        if intent == "GIT_STATUS":
            actions = ("Check Git status",)
        elif intent == "PROJECT_SEARCH":
            query = self._project_search_query(text)
            actions = (f"Search project source files for: {query}",)
        elif intent == "FILE_READ":
            path = self._file_path(text)
            actions = (f"Read file: {path}",)
        elif not actions:
            actions = (
                "Clarify the objective and success criteria",
                "Choose the smallest executable next step",
                "Verify the outcome before declaring success",
            )
        confidence = 0.85 if intent != "UNKNOWN" else 0.55
        if not text:
            confidence = 0.20
        return ReasoningResult(goal=goal, assumptions=tuple(assumptions), constraints=tuple(constraints), next_actions=actions, confidence=confidence)
