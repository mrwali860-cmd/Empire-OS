"""Verification primitives for Empire Brain reasoning."""

from __future__ import annotations

from typing import Any


class ReasoningVerifier:
    """Reject incomplete reasoning results before execution."""

    REQUIRED_FIELDS = (
        "goal",
        "next_actions",
        "confidence",
    )

    def verify(self, result: dict[str, Any]) -> dict[str, Any]:
        missing = [field for field in self.REQUIRED_FIELDS if field not in result]
        actions = result.get("next_actions")
        confidence = result.get("confidence")

        if missing:
            return {
                "verified": False,
                "reason": f"Missing fields: {', '.join(missing)}",
            }

        if not isinstance(actions, list) or not actions:
            return {
                "verified": False,
                "reason": "Reasoning produced no executable next actions.",
            }

        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            return {
                "verified": False,
                "reason": "Confidence must be between 0.0 and 1.0.",
            }

        return {
            "verified": True,
            "reason": "Reasoning structure is valid.",
        }
