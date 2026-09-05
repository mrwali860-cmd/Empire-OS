"""Intent detection for Empire Brain."""

from __future__ import annotations

from typing import Any

from .llm import LLMClient, LLMConfigError, LLMProviderError


class IntentDetector:
    """Classify user intent with an LLM and a deterministic fallback."""

    ALLOWED_INTENTS = {
        "CLIENT_ACQUISITION",
        "REVENUE_GROWTH",
        "SYSTEM_BUILDING",
        "MARKETING",
        "HIRING",
        "GIT_STATUS",
        "UNKNOWN",
    }

    KEYWORDS = {
        "GIT_STATUS": ("git status", "repository status", "repo status", "working tree", "changed files", "branch status"),
        "CLIENT_ACQUISITION": ("client", "customer", "prospect", "lead"),
        "REVENUE_GROWTH": ("revenue", "income", "sales", "profit"),
        "SYSTEM_BUILDING": ("system", "software", "platform", "build"),
        "MARKETING": ("marketing", "advertising", "campaign", "content"),
        "HIRING": ("hire", "hiring", "employee", "team"),
    }

    def __init__(self, llm=None):
        self.llm = llm or LLMClient()

    def _fallback(self, user_input: str) -> str:
        text = user_input.lower()
        for intent, keywords in self.KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return intent
        return "UNKNOWN"

    def detect(self, user_input: str) -> str:
        """Return a normalized intent; deterministic capability signals take precedence."""
        text = (user_input or "").strip()
        if not text:
            return "UNKNOWN"

        deterministic_intent = self._fallback(text)
        if deterministic_intent == "GIT_STATUS":
            print("Intent Source: DETERMINISTIC_FALLBACK (GIT_STATUS)")
            return deterministic_intent

        try:
            result: dict[str, Any] = self.llm.classify_intent(text)
            intent = str(result.get("intent", "UNKNOWN")).upper().strip()
            confidence = float(result.get("confidence", 0.0))
            if intent in self.ALLOWED_INTENTS and 0.0 <= confidence <= 1.0:
                print(f"Intent Source: LLM ({confidence:.2f})")
                return intent
        except (LLMConfigError, LLMProviderError, ValueError, TypeError, KeyError) as exc:
            print(f"LLM intent unavailable: {exc}")

        print(f"Intent Source: DETERMINISTIC_FALLBACK ({deterministic_intent})")
        return deterministic_intent
