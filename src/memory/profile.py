"""
Founder Profile Memory
======================

Stores permanent founder information.
"""


class FounderProfile:

    def __init__(self):

        self.name = "Mr. Wali"

        self.vision = ""

        self.mission = ""

        self.business = ""

        self.primary_goal = ""

    def get_profile(self):

        return {
            "name": self.name,
            "vision": self.vision,
            "mission": self.mission,
            "business": self.business,
            "primary_goal": self.primary_goal
        }

    def update_profile(self, key, value):

        if hasattr(self, key):
            setattr(self, key, value)

    def status(self):

        return "PROFILE READY"