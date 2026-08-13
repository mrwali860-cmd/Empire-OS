"""
decision_engine.py

Empire OS
Decision Engine

Purpose:
Coordinates the entire business decision pipeline.

Author: Empire OS
Version: 1.0
"""

from __future__ import annotations

from .context import ContextAnalyzer
from .evaluator import OpportunityEvaluator
from .explanation import ExplanationEngine
from .models import (
    DecisionReport,
)
from .ranking import RankingEngine
from .recommender import RecommendationEngine
from .report import ReportEngine


class DecisionEngine:
    """
    Empire Business Decision Engine.
    """

    def __init__(self):

        self.context = ContextAnalyzer()

        self.evaluator = OpportunityEvaluator()

        self.ranking = RankingEngine()

        self.recommender = RecommendationEngine()

        self.explainer = ExplanationEngine()

        self.report = ReportEngine()

    # -------------------------------------------------

    def recommend(
        self,
        raw_context,
        options,
    ):

        context = self.context.understand(
            raw_context
        )

        evaluated_results = []

        for option in options:

            result = self.evaluator.evaluate(
                option=option,

                roi=option.roi,

                risk=option.risk,

                alignment=option.alignment,

                impact=option.impact,

                execution_time=option.execution_time,

                cost=option.cost,
            )

            result.reasons = self.explainer.explain(
                result
            )

            evaluated_results.append(result)

        ranked = self.ranking.rank(
            evaluated_results
        )

        recommendation = self.recommender.recommend(
            ranked
        )

        decision_report = DecisionReport(

            context=context,

            recommended=recommendation,

            alternatives=self.recommender.alternatives(
                ranked
            ),

        )

        return self.report.build(
            decision_report
        )