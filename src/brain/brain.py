"""
Empire Brain
============

Central Intelligence Controller

Responsibilities:
- Receive requests
- Start the thinking pipeline
- Return the final response
"""

from .pipeline import BrainPipeline


class EmpireBrain:

    def __init__(self):
        self.pipeline = BrainPipeline()

    def think(self, user_input: str):
        """
        Main entry point of Empire Brain.
        """

        return self.pipeline.process(user_input)