"""
Empire OS Error Handler
=======================

Responsible for handling system errors safely.
"""


from datetime import datetime, timezone


class ErrorHandler:

    def __init__(self):

        self.errors = []

    # --------------------------------
    # Record Error
    # --------------------------------

    def record(self, module, message):

        error = {
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "module": module,
            "message": message
        }

        self.errors.append(error)

        print(f"[ERROR] {module}: {message}")

    # --------------------------------
    # Get Errors
    # --------------------------------

    def get_errors(self):

        return self.errors

    # --------------------------------
    # Latest Error
    # --------------------------------

    def latest(self):

        if self.errors:
            return self.errors[-1]

        return None

    # --------------------------------
    # Clear Errors
    # --------------------------------

    def clear(self):

        self.errors.clear()

    # --------------------------------
    # Status
    # --------------------------------

    def status(self):

        return {
            "status": "READY",
            "errors": len(self.errors)
        }