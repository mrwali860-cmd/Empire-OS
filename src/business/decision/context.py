"""
context.py

Empire OS
Decision Context Analyzer

Purpose:
Understand the complete business situation
before any decision is made.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# -------------------------------------------------
# Business Context
# -------------------------------------------------

@dataclass(slots=True)
class BusinessContext:

    goal: str = ""

    business_stage: str = ""

    industry: str = ""

    available_budget: float = 0.0

    available_team: int = 0

    urgency: str = "normal"

    decision_category: str = ""

    current_problem: str = ""

    founder_constraints: list[str] = None

    metadata: dict[str, Any] = None


# -------------------------------------------------
# Context Analyzer
# -------------------------------------------------

class ContextAnalyzer:
    """
    Converts raw founder input
    into structured business context.
    """

    def understand(
        self,
        raw_context: dict[str, Any]
    ) -> BusinessContext:

        context = BusinessContext()

        context.goal = raw_context.get("goal", "")

        context.business_stage = raw_context.get(
            "business_stage",
            ""
        )

        context.industry = raw_context.get(
            "industry",
            ""
        )

        context.available_budget = raw_context.get(
            "available_budget",
            0.0
        )

        context.available_team = raw_context.get(
            "available_team",
            0
        )

        context.current_problem = raw_context.get(
            "problem",
            ""
        )

        context.founder_constraints = raw_context.get(
            "constraints",
            []
        )

        context.metadata = raw_context.get(
            "metadata",
            {}
        )

        context.urgency = self.detect_urgency(context)

        context.decision_category = self.detect_category(context)

        return context

    # -------------------------------------------------

    def detect_urgency(
        self,
        context: BusinessContext
    ) -> str:

        if "loss" in context.current_problem.lower():
            return "high"

        if "urgent" in context.current_problem.lower():
            return "high"

        return "normal"

    # -------------------------------------------------

    def detect_category(
        self,
        context: BusinessContext
    ) -> str:

        goal = context.goal.lower()

        if "growth" in goal:
            return "growth"

        if "revenue" in goal:
            return "revenue"

        if "profit" in goal:
            return "profit"

        if "client" in goal:
            return "client"

        if "automation" in goal:
            return "automation"

        return "general"
    