"""
Empire OS

Decision Evaluator Tests
"""

import unittest

from src.business.decision.evaluator import OpportunityEvaluator
from src.business.decision.models import DecisionOption


class TestOpportunityEvaluator(unittest.TestCase):

    def setUp(self):

        self.evaluator = OpportunityEvaluator()

        self.option = DecisionOption(

            id="OP001",

            title="Launch New Product",

            description="New AI Product",

            roi=90,

            risk=20,

            alignment=95,

            impact=85,

            execution_time=35,

            cost=30,

        )

    # -------------------------------------------------

    def test_evaluation_returns_result(self):

        result = self.evaluator.evaluate(

            option=self.option,

            roi=self.option.roi,

            risk=self.option.risk,

            alignment=self.option.alignment,

            impact=self.option.impact,

            execution_time=self.option.execution_time,

            cost=self.option.cost,

        )

        self.assertIsNotNone(result)

    # -------------------------------------------------

    def test_final_score_exists(self):

        result = self.evaluator.evaluate(

            option=self.option,

            roi=self.option.roi,

            risk=self.option.risk,

            alignment=self.option.alignment,

            impact=self.option.impact,

            execution_time=self.option.execution_time,

            cost=self.option.cost,

        )

        self.assertGreaterEqual(

            result.score.final_score,

            0

        )

        self.assertLessEqual(

            result.score.final_score,

            100

        )

    # -------------------------------------------------

    def test_confidence_exists(self):

        result = self.evaluator.evaluate(

            option=self.option,

            roi=self.option.roi,

            risk=self.option.risk,

            alignment=self.option.alignment,

            impact=self.option.impact,

            execution_time=self.option.execution_time,

            cost=self.option.cost,

        )

        self.assertGreaterEqual(

            result.confidence,

            0

        )

        self.assertLessEqual(

            result.confidence,

            100

        )

    # -------------------------------------------------

    def test_option_is_preserved(self):

        result = self.evaluator.evaluate(

            option=self.option,

            roi=self.option.roi,

            risk=self.option.risk,

            alignment=self.option.alignment,

            impact=self.option.impact,

            execution_time=self.option.execution_time,

            cost=self.option.cost,

        )

        self.assertEqual(

            result.option.title,

            "Launch New Product"

        )


if __name__ == "__main__":

    unittest.main()