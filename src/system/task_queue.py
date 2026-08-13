"""
Empire OS Task Queue
====================

Stores and manages tasks waiting for execution.
"""


from datetime import datetime, timezone


class TaskQueue:

    def __init__(self):

        self.queue = []

    # --------------------------------
    # Add Task
    # --------------------------------

    def add(self, task_name, priority="NORMAL", data=None):

        task = {
            "name": task_name,
            "priority": priority.upper(),
            "data": data,
            "created": datetime.now(timezone.utc),
            "status": "PENDING"
        }

        self.queue.append(task)

        print(f"✓ Task Added -> {task_name}")

    # --------------------------------
    # Get Next Task
    # --------------------------------

    def next_task(self):

        if not self.queue:
            return None

        return self.queue.pop(0)

    # --------------------------------
    # Queue Size
    # --------------------------------

    def size(self):

        return len(self.queue)

    # --------------------------------
    # Clear Queue
    # --------------------------------

    def clear(self):

        self.queue.clear()

    # --------------------------------
    # View Queue
    # --------------------------------

    def all_tasks(self):

        return self.queue

    # --------------------------------
    # Status
    # --------------------------------

    def status(self):

        return {
            "status": "READY",
            "tasks": self.size()
        }