"""
Brain Processing Pipeline
"""

from .intent import IntentDetector
from .context import ContextAnalyzer
from .thinking import BusinessThinking
from .decisions import DecisionEngine
from .planner import ExecutionPlanner
from .response import ResponseBuilder


class BrainPipeline:

    def __init__(self):
        self.intent = IntentDetector()
        self.context = ContextAnalyzer()
        self.thinking = BusinessThinking()
        self.decision = DecisionEngine()
        self.planner = ExecutionPlanner()
        self.response = ResponseBuilder()

    def process(self, user_input):

        print("Pipeline Started")

        # Step 1 - Detect Intent
        intent = self.intent.detect(user_input)
        print(f"Intent: {intent}")

        # Step 2 - Analyze Context
        context = self.context.analyze(user_input)
        print(f"Context: {context}")

        # Step 3 - Business Thinking
        thinking_result = self.thinking.think(intent, context)
        print(f"Thinking: {thinking_result}")

        # Step 4 - Decision
        decision = self.decision.decide(thinking_result)
        print(f"Decision: {decision}")

        # Step 5 - Planning
        plan = self.planner.plan(decision)
        print(f"Plan: {plan}")

        # Step 6 - Response
        response = self.response.build(plan, context)
        print(f"Response: {response}")

        return response