from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.card_simulator.data.component import TimeStore, AmmoComponent, ValueStore
    from event import EventBus, EventFilter

class Condition(ABC):
    @abstractmethod
    def is_met(self) -> bool:
        """
        Returns True if the condition is currently satisfied.
        Does NOT modify any state.
        """
        ...

class TimeCondition(Condition):
    """
    Checks if the item has charged enough to fire.
    """
    def __init__(self, cooldown_key: str, time_store: TimeStore, value_store: ValueStore):
        self.cooldown_key = cooldown_key
        self.time_store = time_store
        self.value_store = value_store

    def is_met(self) -> bool:
        # Wir holen den aktuellen Max Cooldown (kann sich durch Skills ändern)
        max_cooldown_seconds = self.value_store.get(self.cooldown_key)
        # Progress in Seconds vergleichen
        return self.time_store.progress_in_seconds >= max_cooldown_seconds

class AmmoCondition(Condition):
    """
    Checks if the item has ammo.
    """
    def __init__(self, ammo_component: AmmoComponent):
        self.ammo_component = ammo_component

    def is_met(self) -> bool:
        return self.ammo_component.has_ammo()

class CombinedCondition(Condition):
    def __init__(self, conditions: List[Condition], operator = 'and'):
        self.conditions = conditions
        self.operator = operator

    def is_met(self) -> bool:
        if self.operator == 'and':
            return all(c.is_met() for c in self.conditions)
        elif self.operator == 'or':
            return any(c.is_met() for c in self.conditions)
        return False
