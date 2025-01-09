from abc import ABC, abstractmethod


class Event:
    def __init__(self, name, **params):
        self.name = name
        self.params = params


class Subscriber(ABC):
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.handled_events = set()

    @abstractmethod
    def handle(self, event):
        pass

    def can_handle(self, event: Event):
        return event.name in self.handled_events


class EventBus:
    def __init__(self):
        self.subscribers_list = []

    def register(self, member: Subscriber):
        self.subscribers_list.append(member)

    def dispatch(self, event):
        for sub in self.subscribers_list:
            if sub.can_handle(event):
                sub.handle(event)
