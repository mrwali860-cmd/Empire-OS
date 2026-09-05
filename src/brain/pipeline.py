"""Brain Processing Pipeline."""

from .context import ContextAnalyzer
from .decisions import DecisionEngine
from .intent import IntentDetector
from .llm import LLMClient, LLMConfigError, LLMProviderError
from .planner import ExecutionPlanner
from .response import ResponseBuilder
from .thinking import BusinessThinking
from .reasoning import ReasoningEngine, ReasoningVerifier, ReasoningResult
from ..agent.orchestrator import EmpireOrchestrator


class BrainPipeline:
    """Process requests through reasoning, planning, and optional execution."""

    def __init__(self, llm=None, intent_llm=None, orchestrator=None):
        self.llm = llm or LLMClient()
        self.intent = IntentDetector(llm=intent_llm or self.llm)
        self.context = ContextAnalyzer()
        self.thinking = BusinessThinking()
        self.reasoning = ReasoningEngine()
        self.verifier = ReasoningVerifier()
        self.decision = DecisionEngine()
        self.planner = ExecutionPlanner()
        self.orchestrator = orchestrator or EmpireOrchestrator()
        self.response = ResponseBuilder()

    def _reason(self, user_input, intent, context, thinking_result):
        payload = {
            "user_input": user_input,
            "intent": intent,
            "context": context,
            "current_strategy": thinking_result,
        }

        try:
            llm_output = self.llm.reason(payload)
            result = ReasoningResult(
                goal=str(llm_output.get("goal", user_input.strip())),
                assumptions=tuple(str(x) for x in llm_output.get("assumptions", [])),
                constraints=tuple(str(x) for x in llm_output.get("constraints", [])),
                next_actions=tuple(str(x) for x in llm_output.get("next_actions", [])),
                confidence=float(llm_output.get("confidence", 0.0)),
            )
            check = self.verifier.verify(result.as_dict())
            if check["verified"]:
                print("Reasoning Source: LLM")
                return result
            print(f"LLM reasoning rejected: {check['reason']}")
        except (LLMConfigError, LLMProviderError, ValueError, TypeError, KeyError) as exc:
            print(f"LLM unavailable: {exc}")

        fallback = self.reasoning.reason(
            user_input=user_input,
            intent=intent,
            context=context,
            thinking_result=thinking_result,
        )
        print("Reasoning Source: DETERMINISTIC_FALLBACK")
        return fallback

    def process(self, user_input, *, execute=False, approved=False, executor=None, task_verifier=None):
        """Process a request and optionally execute its validated plan.

        Execution is opt-in. When enabled, the orchestrator uses its
        allow-listed capability layer unless an executor is explicitly
        injected for testing or specialized integrations.
        """
        print("Pipeline Started")

        intent = self.intent.detect(user_input)
        print(f"Intent: {intent}")

        context = self.context.analyze(user_input)
        print(f"Context: {context}")

        thinking_result = self.thinking.think(intent, context)
        print(f"Thinking: {thinking_result}")

        reasoning_result = self._reason(
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

        decision = self.decision.decide(reasoning_result.summary())
        print(f"Decision: {decision}")

        plan = self.planner.plan(decision)
        print(f"Plan: {plan}")

        orchestration_result = None
        if execute and plan.get("status") == "READY":
            orchestration_result = self.orchestrator.execute_plan(
                plan,
                executor=executor,
                verifier=task_verifier,
                approved=approved,
            )
            print(f"Orchestration: {orchestration_result}")

        response = self.response.build(
            plan,
            context,
            orchestration_result=orchestration_result,
        )
        print(f"Response: {response}")

        return response
