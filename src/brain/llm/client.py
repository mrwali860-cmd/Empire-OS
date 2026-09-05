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


class LLMClient:
    """Small OpenAI Responses API adapter with structured JSON output."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("EMPIRE_LLM_MODEL", "gpt-5.6-luna")
        self.api_key = os.getenv("OPENAI_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def reason(self, payload: dict[str, Any]) -> dict[str, Any]:
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

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            instructions=(
                "You are the reasoning core of Empire OS. "
                "Analyze the user's objective, use the supplied context, "
                "state assumptions and constraints, and produce a small "
                "testable action plan. Do not claim an action was executed. "
                "Return only valid JSON with keys: goal, assumptions, "
                "constraints, next_actions, confidence. confidence must be "
                "a number from 0 to 1 and next_actions must be a non-empty array."
            ),
            input=json.dumps(payload, ensure_ascii=False),
        )

        raw = response.output_text.strip()
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMConfigError("LLM returned non-JSON reasoning output.") from exc

        if not isinstance(result, dict):
            raise LLMConfigError("LLM reasoning output must be a JSON object.")

        return result
