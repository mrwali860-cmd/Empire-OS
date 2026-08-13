"""
recommender.py

Empire OS
Business Recommendation Engine

Purpose:
Generate the final business recommendation
from ranked decision results.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

from .models import (
    DecisionResult,
)


class RecommendationEngine:
    """
    Empire Recommendation Engine.
    """

    # -------------------------------------------------
    # Recommend
    # -------------------------------------------------

    def recommend(
        self,
        ranked_results: list[DecisionResult],
    ) -> DecisionResult | None:
        """
        Return the best recommendation.
        """

        if not ranked_results:
            return None

        best = ranked_results[0]

        if not self.is_recommendable(best):
            return None

        return best

    # -------------------------------------------------
    # Recommendation Validation
    # -------------------------------------------------

    def is_recommendable(
        self,
        result: DecisionResult,
    ) -> bool:
        """
        Validate recommendation quality.
        """

        if result.confidence < 50:
            return False

        if result.score.risk > 90:
            return False

        return result.score.final_score >= 50

    # -------------------------------------------------
    # Alternative Recommendations
    # -------------------------------------------------

    def alternatives(
        self,
        ranked_results: list[DecisionResult],
        limit: int = 2,
    ) -> list[DecisionResult]:
        """
        Return alternative recommendations.
        """

        return ranked_results[1:limit + 1]
