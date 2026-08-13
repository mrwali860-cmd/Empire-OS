"""
Empire OS Health Monitor
========================

Monitors the health of every Empire OS module.
"""


class HealthMonitor:

    def __init__(self):

        self.components = {}

    # --------------------------------
    # Register Component
    # --------------------------------

    def register(self, name, status="HEALTHY"):

        self.components[name] = status

    # --------------------------------
    # Update Status
    # --------------------------------

    def update(self, name, status):

        if name in self.components:
            self.components[name] = status

    # --------------------------------
    # Get Status
    # --------------------------------

    def get_status(self, name):

        return self.components.get(name, "UNKNOWN")

    # --------------------------------
    # Full Report
    # --------------------------------

    def report(self):

        return self.components

    # --------------------------------
    # Check Overall Health
    # --------------------------------

    def overall_status(self):

        if all(status == "HEALTHY" for status in self.components.values()):
            return "SYSTEM HEALTHY"

        return "ATTENTION REQUIRED"