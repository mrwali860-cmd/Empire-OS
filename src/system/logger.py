"""
Empire OS Logger
================

Records every important activity inside Empire OS.
"""


from datetime import datetime, timezone


class EmpireLogger:

    def __init__(self):

        self.logs = []

    # --------------------------
    # Add Log
    # --------------------------

    def log(self, level, message):

        entry = {
    "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    "level": level.upper(),
    "message": message,
}

        self.logs.append(entry)

        print(f"[{entry['level']}] {entry['message']}")

    # --------------------------
    # Info
    # --------------------------

    def info(self, message):

        self.log("INFO", message)

    # --------------------------
    # Warning
    # --------------------------

    def warning(self, message):

        self.log("WARNING", message)

    # --------------------------
    # Error
    # --------------------------

    def error(self, message):

        self.log("ERROR", message)

    # --------------------------
    # Get Logs
    # --------------------------

    def get_logs(self):

        return self.logs

    # --------------------------
    # Clear Logs
    # --------------------------

    def clear(self):

        self.logs.clear()

    # --------------------------
    # Status
    # --------------------------

    def status(self):

        return {
            "logs": len(self.logs),
            "status": "READY"
        }