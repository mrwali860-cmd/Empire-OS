"""
Empire OS Scheduler
===================

Responsible for scheduling recurring tasks inside Empire OS.
"""

from datetime import datetime, timezone


class EmpireScheduler:

    def __init__(self):

        self.tasks = []

    # --------------------------------
    # Add Task
    # --------------------------------

    def add_task(self, name, interval, action):

        task = {
            "name": name,
            "interval": interval,
            "action": action,
            "created": datetime.now(timezone.utc),
            "enabled": True
        }

        self.tasks.append(task)

        print(f"✓ Task Scheduled -> {name}")

    # --------------------------------
    # Remove Task
    # --------------------------------

    def remove_task(self, name):

        self.tasks = [
            task for task in self.tasks
            if task["name"] != name
        ]

        print(f"✓ Task Removed -> {name}")

    # --------------------------------
    # Enable Task
    # --------------------------------

    def enable(self, name):

        for task in self.tasks:
            if task["name"] == name:
                task["enabled"] = True

    # --------------------------------
    # Disable Task
    # --------------------------------

    def disable(self, name):

        for task in self.tasks:
            if task["name"] == name:
                task["enabled"] = False

    # --------------------------------
    # List Tasks
    # --------------------------------

    def list_tasks(self):

        return self.tasks

    # --------------------------------
    # Run Scheduler
    # --------------------------------

    def run(self):

        print("Scheduler Running...")

        for task in self.tasks:

            if task["enabled"]:

                print(f"Running -> {task['name']}")

    # --------------------------------
    # Status
    # --------------------------------

    def status(self):

        return {
            "status": "READY",
            "tasks": len(self.tasks)
        }