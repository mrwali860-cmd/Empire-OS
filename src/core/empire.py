from src.brain.brain import EmpireBrain
from src.config import Config
from src.memory.memory import EmpireMemory


class Empire:

    def __init__(self):
        self.version = Config.VERSION
        self.brain = EmpireBrain()
        self.memory = EmpireMemory()
    def start(self):

        Config.show_info()

        print("\nInitializing Empire OS...\n")

        print("✓ Configuration Loaded")

        memory_status = self.memory.status()

        print(memory_status)

        print("✓ Memory Ready")
        print("✓ Empire Brain Ready")
        print("✓ Memory Ready")
        print("✓ Empire Brain Ready")
        print("✓ AI Workers Ready")
        print("✓ Automation Engine Ready")

        print(f"\n{Config.STARTUP_MESSAGE}\n")

        user_input = input("Founder > ")

        result = self.brain.think(user_input)

        print(result)

        print(result)