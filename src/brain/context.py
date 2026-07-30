class ContextAnalyzer:

    def analyze(self, user_input):

        context = {
            "experience": "UNKNOWN",
            "budget": "UNKNOWN",
            "business": "UNKNOWN",
            "urgency": "UNKNOWN",
            "resources": "UNKNOWN"
        }

        text = user_input.lower()

        if "first client" in text:
            context["experience"] = "BEGINNER"

        if "agency" in text:
            context["business"] = "AGENCY"

        if "saas" in text:
            context["business"] = "SAAS"

        if "urgent" in text:
            context["urgency"] = "HIGH"

        return context