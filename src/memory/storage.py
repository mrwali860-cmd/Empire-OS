"""
Memory Storage
==============

Responsible for saving and loading memory.

Version 1:
JSON Storage (Coming Soon)
"""


class MemoryStorage:

    def __init__(self):

        self.storage_type = "JSON"

    def save(self, data):

        print("Memory Saved")

    def load(self):

        print("Memory Loaded")

        return {}

    def status(self):

        return {
            "storage": self.storage_type,
            "status": "READY"
        }