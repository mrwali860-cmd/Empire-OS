class DecisionEngine:

    def decide(self, thinking_result):

        if not thinking_result:
            return {
                "status": "FAILED",
                "decision": "No decision available."
            }

        return {
            "status": "APPROVED",
            "decision": thinking_result
        }