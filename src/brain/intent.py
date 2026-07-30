class IntentDetector:

    def detect(self, user_input):

        text = user_input.lower()

        if "client" in text:
            return "CLIENT_ACQUISITION"

        elif "revenue" in text:
            return "REVENUE_GROWTH"

        elif "system" in text:
            return "SYSTEM_BUILDING"

        elif "marketing" in text:
            return "MARKETING"

        elif "hire" in text:
            return "HIRING"

        return "UNKNOWN"