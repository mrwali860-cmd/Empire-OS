"""
models.py

Empire OS
Decision Models

Purpose:
Defines all data models used by the Decision Engine.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# -------------------------------------------------
# Business Goal
# -------------------------------------------------

@dataclass(slots=True)
class BusinessGoal:
    """
    Represents the primary business objective.
    """

    name: str
    priority: int = 100
    description: str = ""


# -------------------------------------------------
# Decision Context
# -------------------------------------------------

@dataclass(slots=True)
class DecisionContext:
    """
    Complete business context before making a decision.
    """

    business_id: str

    founder_id: str

    goal: BusinessGoal

    available_budget: float = 0.0

    available_team: int = 0

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)


# -------------------------------------------------
# Decision Option
# -------------------------------------------------

@dataclass(slots=True)
class DecisionOption:
    """
    One possible business decision.
    """

    id: str
    title: str
    description: str = ""

    roi: float = 0.0
    risk: float = 0.0
    alignment: float = 0.0
    impact: float = 0.0
    execution_time: float = 0.0
    cost: float = 0.0


# -------------------------------------------------
# Decision Score
# -------------------------------------------------

@dataclass(slots=True)
class DecisionScore:
    """
    Stores all evaluation metrics.
    """

    roi: float = 0.0

    risk: float = 0.0

    cost: float = 0.0

    execution_time: float = 0.0

    complexity: float = 0.0

    alignment: float = 0.0

    business_impact: float = 0.0

    final_score: float = 0.0


# -------------------------------------------------
# Decision Result
# -------------------------------------------------

@dataclass(slots=True)
class DecisionResult:
    """
    Final evaluated decision.
    """

    option: DecisionOption

    score: DecisionScore

    confidence: float = 0.0

    reasons: list[str] = field(default_factory=list)

    risks: list[str] = field(default_factory=list)

    expected_results: list[str] = field(default_factory=list)


# -------------------------------------------------
# Decision Report
# -------------------------------------------------

@dataclass(slots=True)
class DecisionReport:
    """
    Final report shown to Founder.
    """

    context: DecisionContext

    recommended: DecisionResult

    alternatives: list[DecisionResult] = field(default_factory=list)

    generated_at: datetime = field(default_factory=datetime.utcnow)
    