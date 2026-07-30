class ExecutionPlanner:

    def plan(self, decision):

        if decision["status"] != "APPROVED":
            return {
                "status": "FAILED",
                "tasks": []
            }

        return {
            "status": "READY",
            "tasks": decision["decision"]
        }