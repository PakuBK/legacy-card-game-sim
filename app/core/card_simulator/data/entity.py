from __future__ import annotations

from typing import List, Type, TypeVar, TYPE_CHECKING


if TYPE_CHECKING:
    from component import Component
    T = TypeVar("T", bound=Component)
    from action import Action


class Entity:
    def __init__(self, components: List[Type[Component]] = None, tick_size: float = 0.1):
        """
        Constructor of Entity, you can pass Component Type for quick initialization.
        WARNING: Only works with Component that don't override the constructor.
        :param components:
        :param tick_size:
        """
        if components is None:
            components = []
        self.tick_size = tick_size
        self.components: List[Component] = list()
        for comp in components:
            self.components.append(comp(self))
        self.actions: List[Action] = list()

    def get_component(self, component_type: Type[T]) -> T | None:
        for component in self.components:
            if type(component) == component_type:
                return component
        return None

    def add_component(self, component: T) -> T:
        self.components.append(component)
        return component

    def add_action(self, action: Action) -> None:
        self.actions.append(action)

    def __repr__(self):
        res = "-- Entity -- \n"
        for comp in self.components:
            res += repr(comp) + "\n"
        return res

    def update(self, context) -> None:
        # we update the state of the components
        for component in self.components:
            component.update(context)
        for action in self.actions:
            action.try_execute(context)





