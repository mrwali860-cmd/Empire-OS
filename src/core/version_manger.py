"""
Empire OS Version Manager
-------------------------
Manages version information of Empire OS.
"""

from config import Config
from core.logger import Logger


class VersionManager:

    @staticmethod
    def show_version():

        Logger.info("Empire OS Version Information")

        print(f"Project : {Config.PROJECT_NAME}")
        print(f"Version : {Config.VERSION}")
        print(f"Founder : {Config.FOUNDER}")

    @staticmethod
    def get_version():

        return Config.VERSION