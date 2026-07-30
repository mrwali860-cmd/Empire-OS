class ResponseBuilder:

    def build(self, plan, context):

        if plan["status"] != "READY":
            return "Unable to generate a response."

        return (
            "\n========== EMPIRE AI ==========\n"
            f"{plan['tasks']}\n\n"
            "Status: READY FOR EXECUTION\n"
            "===============================\n"
        )