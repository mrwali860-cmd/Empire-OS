"""
explanation.py

Empire OS
Decision Explanation Engine

Purpose:
Generate human-readable explanations
for every business recommendation.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

from .models import DecisionResult


class ExplanationEngine:
    """
    Builds explanations for business decisions.
    """

    def explain(
        self,
        result: DecisionResult,
    ) -> list[str]:

        reasons = []

        if result.score.roi >= 80:
            reasons.append(
                "High expected return on investment."
            )

        if result.score.alignment >= 80:
            reasons.append(
                "Strong alignment with founder goals."
            )

        if result.score.business_impact >= 80:
            reasons.append(
                "High positive impact on business growth."
            )

        if result.score.risk <= 30:
            reasons.append(
                "Business risk is relatively low."
            )

        if result.score.execution_time <= 30:
            reasons.append(
                "Can be executed quickly."
            )

        if result.score.cost <= 30:
            reasons.append(
                "Requires relatively low investment."
            )

        if not reasons:
            reasons.append(
                "Balanced recommendation based on overall business evaluation."
            )

        return reasons

    # ---------------------------------------------

    def summarize_risk(
        self,
        result: DecisionResult,
    ) -> str:

        risk = result.score.risk

        if risk <= 20:
            return "Very Low Risk"

        if risk <= 40:
            return "Low Risk"

        if risk <= 60:
            return "Moderate Risk"

        if risk <= 80:
            return "High Risk"

        return "Critical Risk"

    # ---------------------------------------------

    def success_probability(
        self,
        result: DecisionResult,
    ) -> float:

        probability = (
            result.score.final_score
            + result.confidence
        ) / 2

        return round(probability, 2)