"""
History Memory
==============

Stores permanent historical information.
"""


class HistoryMemory:

    def __init__(self):

        self.decisions = []

        self.completed_tasks = []

        self.milestones = []

    def add_decision(self, decision):

        self.decisions.append(decision)

    def add_completed_task(self, task):

        self.completed_tasks.append(task)

    def add_milestone(self, milestone):

        self.milestones.append(milestone)

    def get_history(self):

        return {
            "decisions": self.decisions,
            "completed_tasks": self.completed_tasks,
            "milestones": self.milestones}