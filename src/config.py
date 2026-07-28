"""
Empire OS Configuration
"""

class Config:

    PROJECT_NAME = "Empire OS"
    VERSION = "0.1"
    DESCRIPTION = "Artificial Founder Operating System"

    FOUNDER = "Mr. Wali"

    DEBUG = True

    MEMORY_PATH = "src/memory"
    WORKERS_PATH = "src/workers"
    BUSINESS_PATH = "src/business"
    AUTOMATION_PATH = "src/automation"

    STARTUP_MESSAGE = "Empire OS Started Successfully."

    @classmethod
    def show_info(cls):
        print("=" * 40)
        print(cls.PROJECT_NAME)
        print(cls.DESCRIPTION)
        print(f"Version : {cls.VERSION}")
        print(f"Founder : {cls.FOUNDER}")
        print("=" * 40)