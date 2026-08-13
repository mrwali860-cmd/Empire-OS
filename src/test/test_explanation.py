"""
Empire OS

Explanation Engine Tests
"""

import unittest

from src.business.decision.explanation import ExplanationEngine
from src.business.decision.models import (
    DecisionOption,
    DecisionResult,
    DecisionScore,
)


class TestExplanationEngine(unittest.TestCase):

    def setUp(self):

        self.engine = ExplanationEngine()

        self.result = DecisionResult(

            option=DecisionOption(
                id="OP001",
                title="Launch Product",
                description="",
            ),

            score=DecisionScore(

                roi=90,

                risk=20,

                alignment=95,

                business_impact=88,

                execution_time=25,

                cost=20,

                final_score=91,

            ),

            confidence=94,

        )

    # -------------------------------------------------

    def test_explanation_exists(self):

        reasons = self.engine.explain(
            self.result
        )

        self.assertIsInstance(
            reasons,
            list,
        )

        self.assertGreater(
            len(reasons),
            0,
        )

    # -------------------------------------------------

    def test_low_risk_summary(self):

        summary = self.engine.summarize_risk(
            self.result
        )

        self.assertEqual(
            summary,
            "Very Low Risk",
        )

    # -------------------------------------------------

    def test_success_probability(self):

        probability = self.engine.success_probability(
            self.result
        )

        self.assertGreaterEqual(
            probability,
            0,
        )

        self.assertLessEqual(
            probability,
            100,
        )

    # -------------------------------------------------

    def test_roi_reason_generated(self):

        reasons = self.engine.explain(
            self.result
        )

        self.assertIn(
            "High expected return on investment.",
            reasons,
        )

    # -------------------------------------------------

    def test_alignment_reason_generated(self):

        reasons = self.engine.explain(
            self.result
        )

        self.assertIn(
            "Strong alignment with founder goals.",
            reasons,
        )


if __name__ == "__main__":

    unittest.main()