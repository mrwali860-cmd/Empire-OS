"""
evaluator.py

Empire OS
Business Opportunity Evaluator

Purpose:
Evaluate one business opportunity
using the Business Scoring Engine.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

from .models import (
    DecisionOption,
    DecisionResult,
    DecisionScore,
)
from .scoring import BusinessScoringEngine


class OpportunityEvaluator:
    """
    Empire Opportunity Evaluator.
    """

    def __init__(self):

        self.scoring = BusinessScoringEngine()

    # -------------------------------------------------
    # Evaluate
    # -------------------------------------------------

    def evaluate(

        self,

        option: DecisionOption,

        *,

        roi: float,

        risk: float,

        alignment: float,

        impact: float,

        execution_time: float,

        cost: float,

    ) -> DecisionResult:

        final_score = self.scoring.calculate_final_score(

            roi=roi,

            risk=risk,

            alignment=alignment,

            impact=impact,

            execution_time=execution_time,

            cost=cost,

        )

        score = DecisionScore(

            roi=roi,

            risk=risk,

            alignment=alignment,

            business_impact=impact,

            execution_time=execution_time,

            cost=cost,

            final_score=final_score,

        )

        confidence = self.calculate_confidence(score)

        return DecisionResult(

            option=option,

            score=score,

            confidence=confidence,

        )

    # -------------------------------------------------
    # Confidence
    # -------------------------------------------------

    def calculate_confidence(

        self,

        score: DecisionScore,

    ) -> float:

        confidence = score.final_score

        if score.risk > 80:

            confidence -= 15

        if score.alignment < 40:

            confidence -= 10

        return max(
            0,
            round(confidence, 2),
        )