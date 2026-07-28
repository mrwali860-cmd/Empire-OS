"""
Empire OS Error Handler
-----------------------
Handles all system errors inside Empire OS.
"""

from core.logger import Logger


class ErrorHandler:

    @staticmethod
    def handle(error):

        Logger.error(f"Error: {error}")

    @staticmethod
    def warning(message):

        Logger.warning(message)

    @staticmethod
    def critical(message):

        Logger.error(f"CRITICAL: {message}")