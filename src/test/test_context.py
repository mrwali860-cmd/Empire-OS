"""
Empire OS

Decision Context Tests
"""

import unittest

from src.business.decision.context import (
    ContextAnalyzer,
)


class TestContextAnalyzer(unittest.TestCase):

    def setUp(self):

        self.analyzer = ContextAnalyzer()

    # ---------------------------------------------

    def test_goal_is_detected(self):

        context = self.analyzer.understand({

            "goal": "Increase Revenue"

        })

        self.assertEqual(

            context.goal,

            "Increase Revenue"

        )

    # ---------------------------------------------

    def test_budget_is_loaded(self):

        context = self.analyzer.understand({

            "available_budget": 5000

        })

        self.assertEqual(

            context.available_budget,

            5000

        )

    # ---------------------------------------------

    def test_team_size(self):

        context = self.analyzer.understand({

            "available_team": 8

        })

        self.assertEqual(

            context.available_team,

            8

        )

    # ---------------------------------------------

    def test_urgency_detection(self):

        context = self.analyzer.understand({

            "problem": "Revenue loss"

        })

        self.assertEqual(

            context.urgency,

            "high"

        )

    # ---------------------------------------------

    def test_category_detection(self):

        context = self.analyzer.understand({

            "goal": "Growth"

        })

        self.assertEqual(

            context.decision_category,

            "growth"

        )


if __name__ == "__main__":

    unittest.main()