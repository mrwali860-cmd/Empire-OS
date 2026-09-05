"""Provider-neutral LLM client for Empire Brain.

The rest of Empire OS talks to this interface instead of a model SDK directly.
That keeps the Brain model-agnostic and makes future model routing possible.
"""

from __future__ import annotations

import json
import os
from typing import Any


class LLMConfigError(RuntimeError):
    """Raised when the LLM provider is not configured correctly."""


class LLMProviderError(LLMConfigError):
    """Raised when the configured LLM provider cannot complete a request."""


class LLMClient:
    """Small OpenAI Responses API adapter with structured JSON output."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("EMPIRE_LLM_MODEL", "gpt-5.6-luna")
        self.api_key = os.getenv("OPENAI_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def _request_json(self, *, instructions: str, payload: Any) -> dict[str, Any]:
        if not self.api_key:
            raise LLMConfigError(
                "OPENAI_API_KEY is not configured; using deterministic fallback."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMConfigError(
                "The openai package is not installed. Install the official OpenAI Python SDK."
            ) from exc

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model=self.model,
                instructions=instructions,
                input=json.dumps(payload, ensure_ascii=False),
            )
        except Exception as exc:
            raise LLMProviderError(f"LLM provider request failed: {exc}") from exc

        try:
            result = json.loads(response.output_text.strip())
        except (json.JSONDecodeError, AttributeError) as exc:
            raise LLMProviderError("LLM returned non-JSON output.") from exc

        if not isinstance(result, dict):
            raise LLMProviderError("LLM output must be a JSON object.")
        return result

    def reason(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json(
            instructions=(
                "You are the reasoning core of Empire OS. "
                "Analyze the user's objective, use the supplied context, "
                "state assumptions and constraints, and produce a small "
                "testable action plan. Do not claim an action was executed. "
                "Return only valid JSON with keys: goal, assumptions, "
                "constraints, next_actions, confidence. confidence must be "
                "a number from 0 to 1 and next_actions must be a non-empty array."
            ),
            payload=payload,
        )

    def classify_intent(self, user_input: str) -> dict[str, Any]:
        """Classify the user's primary intent into Empire OS intent labels."""
        return self._request_json(
            instructions=(
                "You are the intent classifier for Empire OS. "
                "Choose exactly one primary intent from: CLIENT_ACQUISITION, "
                "REVENUE_GROWTH, SYSTEM_BUILDING, MARKETING, HIRING, UNKNOWN. "
                "Return only valid JSON with keys intent and confidence. "
                "confidence must be a number from 0 to 1."
            ),
            payload={"user_input": user_input},
        )
