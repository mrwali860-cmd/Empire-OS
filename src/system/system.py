"""
Empire OS System Engine
=======================

Core Operating System
Responsible for managing all Empire modules.
"""

from src.brain.brain import EmpireBrain
from src.memory.memory import EmpireMemory


class EmpireSystem:

    def __init__(self):

        self.status = "OFFLINE"

        self.modules = {}

        self.brain = EmpireBrain()

        self.memory = EmpireMemory()

    # -----------------------------
    # Boot System
    # -----------------------------

    def boot(self):

        print("Starting Empire System...")

        self.status = "ONLINE"

        self.modules["brain"] = self.brain

        self.modules["memory"] = self.memory

        print("Empire System Online")

    # -----------------------------
    # Register Module
    # -----------------------------

    def register_module(self, name, module):

        self.modules[name] = module

        print(f"Module Registered -> {name}")

    # -----------------------------
    # Get Module
    # -----------------------------

    def get_module(self, name):

        return self.modules.get(name)

    # -----------------------------
    # System Status
    # -----------------------------

    def system_status(self):

        return {
            "status": self.status,
            "modules": list(self.modules.keys())
        }

    # -----------------------------
    # Shutdown
    # -----------------------------

    def shutdown(self):

        self.status = "OFFLINE"

        print("Empire System Shutdown")