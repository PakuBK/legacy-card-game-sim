from abc import ABC, abstractmethod
from typing import List
from enum import Enum

class Event:
    class EventType(Enum):
        ON_BURN = 0
        ON_POISON = 1
        ON_REGEN = 2
        ON_USE = 3
        ON_SHIELD = 4

    def __init__(self, event_type: EventType, origin=None, **meta):
        self.event_type = event_type
        self.origin = origin
        self.meta = meta


class EventBus:
    def __init__(self):
        self._event_queue: list[Event] = []

    def emit(self, event: Event):
        self._event_queue.append(event)

    @property
    def event_queue(self):
        return self._event_queue


class EventFilter(ABC):
    @abstractmethod
    def matches(self, event: Event) -> bool:
        """
        Return true if the event matches the filter
        """

class EventTypeFilter(EventFilter):
    def __init__(self, event_type: str):
        self.event_type = event_type

    def matches(self, event: Event) -> bool:
        return event.event_type == self.event_type


class OriginTagFilter(EventFilter):
    def __init__(self, required_tags: List[str], any_=False):
        self.required_tags = required_tags
        self.any_ = any_

    def matches(self, event: Event) -> bool:
        origin = event.origin
        if not origin: return False
        origin_tags = getattr(origin, "tags", [])
        if self.any_:
            return any(tag in origin_tags for tag in self.required_tags)
        else:
            return all(tag in origin_tags for tag in self.required_tags)



class OrFilter(EventFilter):
    def __init__(self, *filter_: EventFilter):
        self.filter_ = filter_

    def matches(self, event: Event) -> bool:
        return any(f.matches(event) for f in self.filter_)



class AndFilter(EventFilter):
    def __init__(self, *filter_: EventFilter):
        self.filter_ = filter_

    def matches(self, event: Event) -> bool:
        return all(f.matches(event) for f in self.filter_)