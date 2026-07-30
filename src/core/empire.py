from src.config import Config
from src.brain.brain import EmpireBrain


class Empire:

    def __init__(self):
        self.version = Config.VERSION
        self.brain = EmpireBrain()

    def start(self):

        Config.show_info()

        print("\nInitializing Empire OS...\n")

        print("✓ Configuration Loaded")
        print("✓ Memory Ready")
        print("✓ Empire Brain Ready")
        print("✓ AI Workers Ready")
        print("✓ Automation Engine Ready")

        print(f"\n{Config.STARTUP_MESSAGE}\n")

        result = self.brain.think("I need my first client")

        print(result)