"""
Empire OS

Decision Ranking Tests
"""

import unittest

from src.business.decision.models import (
    DecisionOption,
    DecisionResult,
    DecisionScore,
)
from src.business.decision.ranking import RankingEngine


class TestRankingEngine(unittest.TestCase):

    def setUp(self):

        self.engine = RankingEngine()

        self.result_a = DecisionResult(
            option=DecisionOption(
                id="A",
                title="Facebook Ads",
                description="",
            ),
            score=DecisionScore(
                final_score=82
            ),
            confidence=85,
        )

        self.result_b = DecisionResult(
            option=DecisionOption(
                id="B",
                title="Hire Sales Team",
                description="",
            ),
            score=DecisionScore(
                final_score=71
            ),
            confidence=80,
        )

        self.result_c = DecisionResult(
            option=DecisionOption(
                id="C",
                title="Launch Product",
                description="",
            ),
            score=DecisionScore(
                final_score=93
            ),
            confidence=95,
        )

        self.results = [

            self.result_a,

            self.result_b,

            self.result_c,

        ]

    # -------------------------------------------------

    def test_rank_results(self):

        ranked = self.engine.rank(
            self.results
        )

        self.assertEqual(

            ranked[0].option.title,

            "Launch Product"

        )

        self.assertEqual(

            ranked[1].option.title,

            "Facebook Ads"

        )

        self.assertEqual(

            ranked[2].option.title,

            "Hire Sales Team"

        )

    # -------------------------------------------------

    def test_best_result(self):

        best = self.engine.best(
            self.results
        )

        self.assertEqual(

            best.option.title,

            "Launch Product"

        )

    # -------------------------------------------------

    def test_top_results(self):

        top = self.engine.top(

            self.results,

            limit=2,

        )

        self.assertEqual(

            len(top),

            2,

        )

        self.assertEqual(

            top[0].option.title,

            "Launch Product"

        )

        self.assertEqual(

            top[1].option.title,

            "Facebook Ads"

        )


if __name__ == "__main__":

    unittest.main()