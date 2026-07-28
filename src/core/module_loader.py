"""
Empire OS Module Loader
-----------------------
Loads all Empire OS modules.
"""

from core.logger import Logger


class ModuleLoader:

    @staticmethod
    def load_core():

        Logger.info("Loading Empire Core...")

    @staticmethod
    def load_memory():

        Logger.info("Loading Memory Module...")

    @staticmethod
    def load_brain():

        Logger.info("Loading Brain Module...")

    @staticmethod
    def load_workers():

        Logger.info("Loading AI Workers...")

    @staticmethod
    def load_business():

        Logger.info("Loading Business Modules...")

    @staticmethod
    def load_automation():

        Logger.info("Loading Automation Engine...")

    @staticmethod
    def load_all():

        Logger.boot("Loading Empire OS Modules...")

        ModuleLoader.load_core()
        ModuleLoader.load_memory()
        ModuleLoader.load_brain()
        ModuleLoader.load_workers()
        ModuleLoader.load_business()
        ModuleLoader.load_automation()

        Logger.success("All Modules Loaded Successfully.")