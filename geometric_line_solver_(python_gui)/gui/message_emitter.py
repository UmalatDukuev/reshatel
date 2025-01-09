from abc import ABC, abstractmethod


class MessageEmitter(ABC):
    def __init__(self, event_bus, handled_events):
        self.event_bus = event_bus
        self.event_bus.register(self)
        self.handled_events = handled_events

    def can_handle(self, event):
        return event.name in self.handled_events

    @abstractmethod
    def handle(self, event):
        pass
