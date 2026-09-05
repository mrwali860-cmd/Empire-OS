class BusinessThinking:

    def think(self, intent, context):

        if intent == "GIT_STATUS":
            return (
                "Goal: Check repository status\n"
                "1. Check Git status"
            )

        if intent == "CLIENT_ACQUISITION":

            if context.get("experience") == "BEGINNER":
                return (
                    "Goal: Get First Client\n"
                    "Step 1: Create 3 Fiverr gigs\n"
                    "Step 2: Send 10 proposals today\n"
                    "Step 3: Improve profile daily"
                )

            return (
                "Goal: Scale Client Acquisition\n"
                "Step 1: Send 50 LinkedIn DMs\n"
                "Step 2: Publish valuable content\n"
                "Step 3: Follow up with prospects"
            )

        elif intent == "REVENUE_GROWTH":
            return (
                "Focus on increasing revenue through upselling, "
                "new offers, and improving conversions."
            )

        elif intent == "SYSTEM_BUILDING":
            return (
                "Document the workflow and automate repetitive tasks."
            )

        elif intent == "MARKETING":
            return (
                "Create consistent content and build brand awareness."
            )

        elif intent == "HIRING":
            return (
                "Define the role, write the job description, and hire slowly."
            )

        return "More information is required before making a strategy."
