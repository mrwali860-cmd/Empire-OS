"""
business.py

Empire OS
Business Module Entry Point

Purpose:
Initialize and start the complete
Empire Business Module.

Author: Empire OS
Version: 1.0
"""

from automation_engine import AutomationEngine
from business_engine import BusinessEngine
from client_engine import ClientEngine
from dashboard_controller import DashboardController
from decision_engine import DecisionEngine
from growth_engine import GrowthEngine
from opportunity_engine import OpportunityEngine
from product_engine import ProductEngine
from risk_engine import RiskEngine
from worker_coordinator import WorkerCoordinator


class Business:

    """
    Empire Business Module.

    This class creates and connects all business engines.
    """

    def __init__(self):

        self.engine = BusinessEngine()

        self.decision = DecisionEngine()

        self.client = ClientEngine()

        self.product = ProductEngine()

        self.opportunity = OpportunityEngine()

        self.growth = GrowthEngine()

        self.risk = RiskEngine()

        self.automation = AutomationEngine()

        self.workers = WorkerCoordinator()

        self.dashboard = DashboardController()

    # -------------------------------------------------
    # Initialize
    # -------------------------------------------------

    def initialize(self):

        self.engine.register_engine(
            "decision",
            self.decision
        )

        self.engine.register_engine(
            "client",
            self.client
        )

        self.engine.register_engine(
            "product",
            self.product
        )

        self.engine.register_engine(
            "opportunity",
            self.opportunity
        )

        self.engine.register_engine(
            "growth",
            self.growth
        )

        self.engine.register_engine(
            "risk",
            self.risk
        )

        self.engine.register_engine(
            "automation",
            self.automation
        )

        self.engine.register_engine(
            "workers",
            self.workers
        )

        self.engine.register_engine(
            "dashboard",
            self.dashboard
        )

        self.engine.initialize()

    # -------------------------------------------------
    # Start
    # -------------------------------------------------

    def start(self):

        self.initialize()

        self.engine.start()

    # -------------------------------------------------
    # Stop
    # -------------------------------------------------

    def stop(self):

        self.engine.stop()


if __name__ == "__main__":

    business = Business()

    business.start()