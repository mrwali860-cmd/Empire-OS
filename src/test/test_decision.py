"""
Empire OS

Decision Engine Integration Tests
"""

import unittest

from src.business.decision.decision_engine import DecisionEngine
from src.business.decision.models import DecisionOption


class TestDecisionEngine(unittest.TestCase):

    def setUp(self):

        self.engine = DecisionEngine()

        self.context = {

            "goal": "Increase Revenue",

            "available_budget": 5000,

            "available_team": 6,

        }

        self.options = [

            DecisionOption(

                id="OP001",

                title="Launch Product",

                description="",

                roi=90,

                risk=20,

                alignment=95,

                impact=88,

                execution_time=25,

                cost=20,

            ),

            DecisionOption(

                id="OP002",

                title="Facebook Ads",

                description="",

                roi=80,

                risk=30,

                alignment=85,

                impact=82,

                execution_time=20,

                cost=25,

            ),

        ]

    # -------------------------------------------------

    def test_pipeline_returns_report(self):

        report = self.engine.recommend(

            raw_context=self.context,

            options=self.options,

        )

        self.assertIsNotNone(

            report

        )

    # -------------------------------------------------

    def test_report_contains_recommendation(self):

        report = self.engine.recommend(

            raw_context=self.context,

            options=self.options,

        )

        self.assertIn(

            "recommendation",

            report,

        )

    # -------------------------------------------------

    def test_business_score_exists(self):

        report = self.engine.recommend(

            raw_context=self.context,

            options=self.options,

        )

        self.assertIn(

            "business_score",

            report,

        )

    # -------------------------------------------------

    def test_confidence_exists(self):

        report = self.engine.recommend(

            raw_context=self.context,

            options=self.options,

        )

        self.assertIn(

            "confidence",

            report,

        )

    # -------------------------------------------------

    def test_alternatives_exist(self):

        report = self.engine.recommend(

            raw_context=self.context,

            options=self.options,

        )

        self.assertIn(

            "alternatives",

            report,

        )


if __name__ == "__main__":

    unittest.main()