"""
Empire OS

Recommendation Engine Tests
"""

import unittest

from src.business.decision.models import (
    DecisionOption,
    DecisionResult,
    DecisionScore,
)
from src.business.decision.recommender import RecommendationEngine


class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):

        self.engine = RecommendationEngine()

        self.best = DecisionResult(

            option=DecisionOption(
                id="OP001",
                title="Launch Product",
                description=""
            ),

            score=DecisionScore(
                final_score=92,
                risk=20
            ),

            confidence=95,
        )

        self.second = DecisionResult(

            option=DecisionOption(
                id="OP002",
                title="Facebook Ads",
                description=""
            ),

            score=DecisionScore(
                final_score=84,
                risk=30
            ),

            confidence=88,
        )

        self.third = DecisionResult(

            option=DecisionOption(
                id="OP003",
                title="Hire Sales Team",
                description=""
            ),

            score=DecisionScore(
                final_score=73,
                risk=40
            ),

            confidence=75,
        )

        self.results = [

            self.best,

            self.second,

            self.third,

        ]

    # -------------------------------------------------

    def test_best_recommendation(self):

        recommendation = self.engine.recommend(
            self.results
        )

        self.assertIsNotNone(
            recommendation
        )

        self.assertEqual(
            recommendation.option.title,
            "Launch Product"
        )

    # -------------------------------------------------

    def test_alternatives(self):

        alternatives = self.engine.alternatives(
            self.results,
            limit=2,
        )

        self.assertEqual(
            len(alternatives),
            2,
        )

        self.assertEqual(
            alternatives[0].option.title,
            "Facebook Ads"
        )

        self.assertEqual(
            alternatives[1].option.title,
            "Hire Sales Team"
        )

    # -------------------------------------------------

    def test_low_confidence_rejected(self):

        self.best.confidence = 40

        recommendation = self.engine.recommend(
            [self.best]
        )

        self.assertIsNone(
            recommendation
        )

    # -------------------------------------------------

    def test_high_risk_rejected(self):

        self.best.score.risk = 95

        recommendation = self.engine.recommend(
            [self.best]
        )

        self.assertIsNone(
            recommendation
        )


if __name__ == "__main__":

    unittest.main()