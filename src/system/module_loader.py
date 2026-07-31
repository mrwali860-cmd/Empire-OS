"""
Empire OS Module Loader
=======================

Responsible for loading and registering all Empire modules.
"""


class ModuleLoader:

    def __init__(self):

        self.modules = {}

    # --------------------------------
    # Register Module
    # --------------------------------

    def register(self, name, module):

        self.modules[name] = module

        print(f"✓ Loaded -> {name}")

    # --------------------------------
    # Get Module
    # --------------------------------

    def get(self, name):

        return self.modules.get(name)

    # --------------------------------
    # Check Module
    # --------------------------------

    def exists(self, name):

        return name in self.modules

    # --------------------------------
    # Remove Module
    # --------------------------------

    def unload(self, name):

        if name in self.modules:

            del self.modules[name]

            print(f"✓ Unloaded -> {name}")

    # --------------------------------
    # Load All
    # --------------------------------

    def load_all(self):

        print("Loading Empire Modules...")

        for module in self.modules:

            print(f"✓ {module}")

        print("All Modules Loaded")

    # --------------------------------
    # Module List
    # --------------------------------

    def list_modules(self):

        return list(self.modules.keys())

    # --------------------------------
    # Status
    # --------------------------------

    def status(self):

        return {
            "loaded_modules": len(self.modules),
            "modules": self.list_modules()
        }