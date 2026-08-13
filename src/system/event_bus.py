"""
event_bus.py

Empire OS
Central communication system for Empire OS.
"""


class EventBus:
    """Central event communication system."""

    def __init__(self):
        self.listeners = {}

    # --------------------------------
    # Subscribe
    # --------------------------------

    def subscribe(self, event_name, callback):
        """Register a callback for an event."""
        if event_name not in self.listeners:
            self.listeners[event_name] = []

        self.listeners[event_name].append(callback)

    # --------------------------------
    # Publish Event
    # --------------------------------

    def publish(self, event_name, data=None):
        """Publish data to all listeners of an event."""
        if event_name not in self.listeners:
            return

        for callback in self.listeners[event_name]:
            callback(data)

    # --------------------------------
    # Remove Listener
    # --------------------------------

    def unsubscribe(self, event_name, callback):
        """Remove a callback from an event."""
        if event_name in self.listeners and callback in self.listeners[event_name]:
            self.listeners[event_name].remove(callback)

    # --------------------------------
    # Status
    # --------------------------------

    def status(self):
        """Return event bus status."""
        return {
            "events": len(self.listeners),
        }