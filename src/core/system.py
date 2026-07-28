"""
Empire OS System Information
----------------------------
Provides basic information about the running system.
"""

import platform
from src.config import Config
from src.core.empire import Empire


class System:

    def show_status(self):
        print("========== SYSTEM STATUS ==========")
        print(f"Project Name : {Config.PROJECT_NAME}")
        print(f"Version      : {Config.VERSION}")
        print(f"Founder      : {Config.FOUNDER}")
        print(f"Operating OS : {platform.system()} {platform.release()}")
        print(f"Python       : {platform.python_version()}")
        print("Status       : ONLINE")
        print("===================================\n")