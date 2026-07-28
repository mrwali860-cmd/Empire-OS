"""
Empire OS Logger
----------------
Central logging system for Empire OS.
"""


class Logger:

    @staticmethod
    def info(message):
        print(f"[INFO] {message}")

    @staticmethod
    def success(message):
        print(f"[SUCCESS] {message}")

    @staticmethod
    def warning(message):
        print(f"[WARNING] {message}")

    @staticmethod
    def error(message):
        print(f"[ERROR] {message}")

    @staticmethod
    def boot(message):
        print(f"[BOOT] {message}")

    @staticmethod
    def shutdown(message):
        print(f"[SHUTDOWN] {message}")