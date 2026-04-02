from __future__ import annotations
from typing import TYPE_CHECKING, List, Callable

if TYPE_CHECKING:
    from .effect import Effect
    from .condition import Condition
    from .entity import Entity

class Action:
    def __init__(self, 
                 entity_ref: Entity,
                 conditions: List[Condition], 
                 costs: List[Callable[[], None]], 
                 effects: List[Effect]):
        """
        :param conditions: Checks that must be True to execute.
        :param costs: Functions that run ONLY if execution happens (e.g. consume ammo, reset time).
        :param effects: The actual outcome (deal damage).
        """
        self._entity_ref = entity_ref
        self._conditions = conditions
        self._costs = costs
        self._effects = effects

    def can_execute(self) -> bool:
        # Check all conditions (AND logic by default here for the main action trigger)
        for condition in self._conditions:
            if not condition.is_met():
                return False
        return True

    def try_execute(self, context) -> bool:
        if self.can_execute():
            # 1. Pay Costs (State changes)
            for cost in self._costs:
                cost()
            
            # 2. Apply Effects
            for effect in self._effects:
                effect.apply(self._entity_ref, context)
            
            return True
        return False