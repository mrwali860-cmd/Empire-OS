"""Brain Processing Pipeline."""

from .context import ContextAnalyzer
from .decisions import DecisionEngine
from .intent import IntentDetector
from .planner import ExecutionPlanner
from .response import ResponseBuilder
from .thinking import BusinessThinking
from .reasoning import ReasoningEngine, ReasoningVerifier


class BrainPipeline:
    """Process a request through analysis, reasoning, decision and planning."""

    def __init__(self):
        self.intent = IntentDetector()
        self.context = ContextAnalyzer()
        self.thinking = BusinessThinking()
        self.reasoning = ReasoningEngine()
        self.verifier = ReasoningVerifier()
        self.decision = DecisionEngine()
        self.planner = ExecutionPlanner()
        self.response = ResponseBuilder()

    def process(self, user_input):
        print("Pipeline Started")

        # 1. Understand the request.
        intent = self.intent.detect(user_input)
        print(f"Intent: {intent}")

        # 2. Build request context.
        context = self.context.analyze(user_input)
        print(f"Context: {context}")

        # 3. Produce the current business strategy.
        thinking_result = self.thinking.think(intent, context)
        print(f"Thinking: {thinking_result}")

        # 4. Convert strategy into explicit, testable reasoning.
        reasoning_result = self.reasoning.reason(
            user_input=user_input,
            intent=intent,
            context=context,
            thinking_result=thinking_result,
        )
        reasoning_dict = reasoning_result.as_dict()
        reasoning_check = self.verifier.verify(reasoning_dict)
        print(f"Reasoning: {reasoning_result.summary()}")
        print(f"Reasoning Verification: {reasoning_check}")

        if not reasoning_check["verified"]:
            return "Reasoning verification failed: " + reasoning_check["reason"]

        # 5. Existing decision layer remains the policy gate.
        decision = self.decision.decide(reasoning_result.summary())
        print(f"Decision: {decision}")

        # 6. Convert the approved reasoning into an execution plan.
        plan = self.planner.plan(decision)
        print(f"Plan: {plan}")

        # 7. Return a verified reasoning-backed response.
        response = self.response.build(plan, context)
        print(f"Response: {response}")

        return response
