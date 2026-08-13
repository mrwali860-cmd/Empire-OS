"""
Empire OS

Decision Report Tests
"""

import unittest

from src.business.decision.models import (
    BusinessGoal,
    DecisionContext,
    DecisionOption,
    DecisionReport,
    DecisionResult,
    DecisionScore,
)
from src.business.decision.report import ReportEngine


class TestReportEngine(unittest.TestCase):

    def setUp(self):

        self.engine = ReportEngine()

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

            reasons=[

                "High ROI",

                "Strong Alignment",

            ],

            risks=[

                "Market Competition",

            ],

            expected_results=[

                "Revenue Growth",

            ],

        )

        self.report = DecisionReport(

        context=DecisionContext(
    business_id="bus_test_123",
    founder_id="fnd_test_123",
    goal=BusinessGoal(
        name="Increase Revenue"
    ),
),

            recommended=self.result,

            alternatives=[],

        )

    # -------------------------------------------------

    def test_report_generation(self):

        report = self.engine.build(
            self.report
        )

        self.assertIsInstance(
            report,
            dict,
        )

    # -------------------------------------------------

    def test_contains_recommendation(self):

        report = self.engine.build(
            self.report
        )

        self.assertEqual(

            report["recommendation"],

            "Launch Product",

        )

    # -------------------------------------------------

    def test_contains_business_score(self):

        report = self.engine.build(
            self.report
        )

        self.assertEqual(

            report["business_score"],

            91,

        )

    # -------------------------------------------------

    def test_founder_summary(self):

        summary = self.engine.founder_summary(
            self.report
        )

        self.assertIn(

            "Launch Product",

            summary,

        )

    # -------------------------------------------------

    def test_export_json(self):

        exported = self.engine.export_json(
            self.report
        )

        self.assertIsNotNone(
            exported
        )


if __name__ == "__main__":

    unittest.main()