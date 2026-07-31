"""
Session Memory
==============

Stores temporary session information.
"""


class SessionMemory:

    def __init__(self):

        self.current_task = ""

        self.current_context = ""

        self.last_input = ""

        self.last_response = ""

    def update(self, task, context, user_input, response):

        self.current_task = task
        self.current_context = context
        self.last_input = user_input
        self.last_response = response

    def get_session(self):

        return {
            "current_task": self.current_task,
            "current_context": self.current_context,
            "last_input": self.last_input,
            "last_response": self.last_response
        }

    def clear(self):

        self.current_task = ""
        self.current_context = ""
        self.last_input = ""
        self.last_response = ""

    def status(self):

        return "SESSION READY"