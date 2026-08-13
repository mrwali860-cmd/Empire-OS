"""
ranking.py

Empire OS
Decision Ranking Engine
"""

from __future__ import annotations

from src.business.decision.models import DecisionResult


class RankingEngine:
    """Empire Ranking Engine."""

    def rank(
        self,
        results: list[DecisionResult],
    ) -> list[DecisionResult]:
        """Rank opportunities from highest score to lowest score."""
        return sorted(
            results,
            key=lambda result: result.score.final_score,
            reverse=True,
        )

    def best(
        self,
        results: list[DecisionResult],
    ) -> DecisionResult | None:
        """Return the highest-ranked opportunity."""
        ranked = self.rank(results)
        return ranked[0] if ranked else None

    def top(
        self,
        results: list[DecisionResult],
        limit: int = 3,
    ) -> list[DecisionResult]:
        """Return the top-ranked opportunities."""
        return self.rank(results)[:limit]