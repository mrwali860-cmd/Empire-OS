"""
Empire OS

Decision Scoring Tests
"""

import unittest

from src.business.decision.scoring import BusinessScoringEngine


class TestBusinessScoring(unittest.TestCase):

    def setUp(self):
        self.engine = BusinessScoringEngine()

    def test_score_is_between_0_and_100(self):

        score = self.engine.calculate_final_score(

            roi=90,

            risk=20,

            alignment=95,

            impact=80,

            execution_time=30,

            cost=20,

        )

        self.assertGreaterEqual(score, 0)

        self.assertLessEqual(score, 100)

    def test_higher_roi_produces_higher_score(self):

        high = self.engine.calculate_final_score(

            roi=90,
            risk=20,
            alignment=90,
            impact=90,
            execution_time=20,
            cost=20,
        )

        low = self.engine.calculate_final_score(

            roi=40,
            risk=20,
            alignment=90,
            impact=90,
            execution_time=20,
            cost=20,
        )

        self.assertGreater(high, low)


if __name__ == "__main__":
    unittest.main()