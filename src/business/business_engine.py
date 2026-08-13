import unittest
from datetime import datetime, timezone

from business.decision.models import DecisionContext, DecisionReport, BusinessGoal
from business.decision.report import ReportEngine


class TestReportEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = ReportEngine()

        # Added required positional arguments: business_id and founder_id
        self.context = DecisionContext(
            business_id="bus_test_123",
            founder_id="fnd_test_123",
            goal=BusinessGoal(name="Increase Revenue"),
        )

        # Mock result if needed for non-empty tests
        self.result = None 

        self.report = DecisionReport(
            context=self.context,
            recommended=self.result,
            alternatives=[],
        )

    def test_build_report_with_none_recommendation(self) -> None:
        """Ensure build completes without throwing AttributeError when recommended is None."""
        output = self.engine.build(self.report)
        self.assertIsNone(output["recommendation"])
        self.assertEqual(output["confidence"], 0)
        self.assertEqual(output["business_score"], 0)


if __name__ == "__main__":
    unittest.main()