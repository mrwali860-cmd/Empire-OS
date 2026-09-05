class BusinessThinking:

    def think(self, intent, context):

        if intent == "GIT_STATUS":
            return "Goal: Check repository status\n1. Check Git status"

        if intent == "PROJECT_SEARCH":
            return "Goal: Find requested code in the project\n1. Search project source files"

        if intent == "CLIENT_ACQUISITION":
            if context.get("experience") == "BEGINNER":
                return "Goal: Get First Client\nStep 1: Create 3 Fiverr gigs\nStep 2: Send 10 proposals today\nStep 3: Improve profile daily"
            return "Goal: Scale Client Acquisition\nStep 1: Send 50 LinkedIn DMs\nStep 2: Publish valuable content\nStep 3: Follow up with prospects"

        elif intent == "REVENUE_GROWTH":
            return "Focus on increasing revenue through upselling, new offers, and improving conversions."
        elif intent == "SYSTEM_BUILDING":
            return "Document the workflow and automate repetitive tasks."
        elif intent == "MARKETING":
            return "Create consistent content and build brand awareness."
        elif intent == "HIRING":
            return "Define the role, write the job description, and hire slowly."
        return "More information is required before making a strategy."
