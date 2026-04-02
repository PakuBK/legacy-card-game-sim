from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, TypedDict

from .const import StatusEffect
from .formatter import component_to_str
from .event import Event

if TYPE_CHECKING:
    from entity import Entity
    from .effect import Effect


class Component(ABC):
    """
    A Component acts a central store for truth. It NEVER modifies outside state.
    A Component only stores and modifies its own state.
    """
    COMPONENT_ID_STACK = 0

    def __init__(self, entity_ref: Entity):
        self.entity_ref = entity_ref
        self.tick_size = entity_ref.tick_size
        self.component_id = Component.COMPONENT_ID_STACK
        Component.COMPONENT_ID_STACK += 1

    @abstractmethod
    def update(self, context):
        """
        MAYBE REMOVE CONTEXT?
        :param context:
        :return:
        """
        ...

class TimeStore(Component):
    def __init__(self, entity_ref):
        super().__init__(entity_ref)
        self.tick_size = 0.1   # Dauer eines Ticks in Sekunden
        self._progress_ticks: float = 0.0              # Basis: wie viele Ticks vergangen sind (immer int)

    def update(self, context):
        # hole den ModifierManager, falls vorhanden
        modifier_manager = self.entity_ref.get_component(ModifierStore) if self.entity_ref else None
        multiplier = modifier_manager.get_multiplier() if modifier_manager else 1.0

        # Tick hochzählen
        self._progress_ticks += multiplier

    def reset_progress(self):
        self._progress_ticks = 0.0

    def reduce_progress(self, seconds: float):
        """Reduces progress by X seconds (used for paying cooldown cost)."""
        reduce_ticks = seconds / self.tick_size
        self._progress_ticks = max(0.0, self._progress_ticks - reduce_ticks)

    @property
    def progress(self) -> float:
        return self._progress_ticks

    @property
    def progress_in_seconds(self) -> float:
        return self._progress_ticks * self.tick_size

    def apply_charge(self, amount_ticks: float) -> None:
        self._progress_ticks += amount_ticks

    def __repr__(self):
        return component_to_str(name="Item Time", ticks=self.progress, seconds=self.progress_in_seconds)


class ModifierStore(Component):
    """
    Manages active modifiers on an Item.
    Supports unique modifiers (fixed multiplier) and stackable ones.
    """
    def __init__(self, entity_ref):
        super().__init__(entity_ref)
        self.modifiers = {}  # dict[str, dict]

    def add_modifier(self, name: str, multiplier: float, duration_seconds: float, unique: bool = True):
        """
        Add a modifier (e.g., slow, haste).
        duration_seconds: how long the modifier lasts in *seconds*.
        unique: True = same modifier refreshes duration; False = stacks multiplicatively.
        """
        duration_ticks = int(duration_seconds / self.tick_size)

        if unique and name in self.modifiers:
            self.modifiers[name]["remaining_ticks"] += duration_ticks
        else:
            self.modifiers[name] = {
                "multiplier": multiplier,
                "remaining_ticks": duration_ticks,
                "unique": unique
            }

    def update(self, context):
        """Advance one simulation tick, reduce all durations."""
        to_remove = []
        for name, mod in self.modifiers.items():
            mod["remaining_ticks"] -= 1
            if mod["remaining_ticks"] <= 0:
                to_remove.append(name)
        for name in to_remove:
            del self.modifiers[name]

    def get_multiplier(self) -> float:
        multiplier = 1.0
        for mod in self.modifiers.values():
            multiplier *= mod["multiplier"]
        return multiplier

    def __repr__(self):
        return component_to_str(name="Modifier Store", modifiers=self.modifiers)


class ValueStore(Component):
    """
    Acts as a central truth for all base values.
    Example Values: Damage, Burn, Poison, Shield, Heal, etc.
    """
    def __init__(self, entity_ref, default_values:dict[str,int] | None = None):
        super().__init__(entity_ref)
        self._values : dict[str, int] = {} if default_values is None else default_values

    def get(self, identifier: str) -> int:
        return self._values.get(identifier, 0)

    def __getitem__(self, identifier: str) -> int:
        return self.get(identifier)

    def update(self, context):
        pass

    def __repr__(self):
        return component_to_str(name="Value Store", values=self._values)


"""
COMPONENTS MADE FOR PLAYER INTERACTIONS
"""


class ShieldComponent(Component):
    """
    Manages the Shield value independently because Shield has unique interactions
    (it protects against Burn/Attacks but is ignored by Poison).
    """
    def __init__(self, entity_ref):
        super().__init__(entity_ref)
        self._value = 0

    @property
    def value(self) -> int:
        return self._value
    
    
    def update(self, context):
        pass

    def add_shield(self, amount: int):
        self._value += amount

    def consume_shield(self, amount: int) -> int:
        """
        Tries to absorb damage. Returns the remaining damage that shield couldn't cover.
        """
        if self._value >= amount:
            self._value -= amount
            return 0
        else:
            remaining_damage = amount - self._value
            self._value = 0
            return remaining_damage
    
    def __repr__(self):
        return component_to_str(name="Shield", value=self._value)


class HealthComponent(Component):
    """
    Core vitality of the entity. 
    Coordinates damage intake by checking for a ShieldComponent.
    """
    def __init__(self, entity_ref: Entity, init_max_health: int = 100):
        super().__init__(entity_ref)
        self._max_health: int = init_max_health
        self._current_health = init_max_health

    @property
    def current_health(self) -> int:
        return self._current_health
    
    @property
    def max_health(self) -> int:
        return self._max_health

    def heal(self, value: int):
        self._current_health = min(self._current_health + value, self._max_health)

    def take_damage(self, value: int, source_type: str = "direct"):
        """
        Applies damage to the entity.
        :param value: Amount of damage.
        :param source_type: 'direct' (attacks/burn) uses shield. 'piercing' (poison) ignores shield.
        """
        final_damage = value
        
        # Logic: Poison ignores shield, everything else hits shield first
        if source_type != "piercing":
            shield_comp = self.entity_ref.get_component(ShieldComponent)
            if shield_comp:
                final_damage = shield_comp.consume_shield(value)
        
        # Apply remaining damage to health
        self._current_health -= final_damage

    def update(self, context):
        # Health usually doesn't update itself over time, 
        # distinct effects (StatusEffectContainer) do that.
        pass

    def __repr__(self):
        return component_to_str(name="Health", current=self._current_health, max=self._max_health)


class StatusEffectContainer(Component):
    """
    Manages time-based effects like Burn, Poison, and Regeneration.
    It holds the values and the timers for when they trigger.
    """
    # Definitions could also be externalized
    EFFECT_CONFIG = {
        "burn":   {"interval": 0.5, "decay": True,  "type": "damage_normal"},
        "poison": {"interval": 1.0, "decay": False, "type": "damage_piercing"},
        "regen":  {"interval": 1.0, "decay": False, "type": "heal"}
    }

    def __init__(self, entity_ref):
        super().__init__(entity_ref)
        # Stores keys like "burn" -> 50
        self.stacks: dict[str, int] = {k: 0 for k in self.EFFECT_CONFIG.keys()}
        # Stores accumulated time in seconds for each effect
        self.timers: dict[str, float] = {k: 0.0 for k in self.EFFECT_CONFIG.keys()}

    def add_stacks(self, effect_name: str, amount: int):
        if effect_name in self.stacks:
            self.stacks[effect_name] += amount

    def get_stacks(self, effect_name: str) -> int:
        return self.stacks.get(effect_name, 0)

    def update(self, context):
        """
        Increases timers and triggers effects if interval is reached.
        """
        health_comp = self.entity_ref.get_component(HealthComponent)
        if not health_comp:
            return

        for effect_name, config in self.EFFECT_CONFIG.items():
            amount = self.stacks[effect_name]
            if amount <= 0:
                self.timers[effect_name] = 0 # Reset timer if no stacks
                continue

            # Advance timer
            self.timers[effect_name] += self.tick_size

            # Check Trigger
            if self.timers[effect_name] >= config["interval"]:
                self._trigger_effect(effect_name, config, health_comp, amount)
                self.timers[effect_name] -= config["interval"] # Keep surplus time

    def _trigger_effect(self, name: str, config: dict, health_comp: HealthComponent, amount: int):
        # 1. Apply Effect
        if config["type"] == "damage_normal":
            health_comp.take_damage(amount, source_type="direct")
        elif config["type"] == "damage_piercing":
            health_comp.take_damage(amount, source_type="piercing")
        elif config["type"] == "heal":
            health_comp.heal(amount)
        
        # 2. Handle Decay (Burn reduces by 1 after triggering)
        if config["decay"]:
            self.stacks[name] = max(0, self.stacks[name] - 1)
            
    def __repr__(self):
        return component_to_str(name="Status Effects", stacks=self.stacks)


class AmmoComponent(Component):
    def __init__(self, entity_ref, max_ammo: int):
        super().__init__(entity_ref)
        self.max_ammo = max_ammo
        self.current_ammo = max_ammo

    def update(self, context):
        pass

    def has_ammo(self) -> bool:
        return self.current_ammo > 0

    def try_consume(self) -> bool:
        if self.current_ammo > 0:
            self.current_ammo -= 1
            return True
        return False

    def reload(self, amount: int):
        self.current_ammo = min(self.current_ammo + amount, self.max_ammo)
    
    def __repr__(self):
        return component_to_str(name="Ammo", current=self.current_ammo, max=self.max_ammo)


class TagComponent(Component):
    """
    Holds tags like 'Weapon', 'Aquatic', 'Food', 'Magic'.
    """
    def __init__(self, entity_ref, tags: List[str] = None):
        super().__init__(entity_ref)
        self.tags = set(tags) if tags else set()

    def update(self, context):
        pass

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def add_tag(self, tag: str):
        self.tags.add(tag)

    def __repr__(self):
        return component_to_str(name="Tags", tags=list(self.tags))



class ItemSize(Component):
    def __init__(self, entity_ref, size: int = 1):  # 1=Small, 2=Medium, 3=Large
        super().__init__(entity_ref)
        self.size = size

    def update(self, context):
        pass

class BoardComponent(Component):
    """
    Component for the PLAYER Entity. Holds references to ITEM Entities.
    The Bazaar Board has a fixed size (starts at 4, grows to 10).
    """
    def __init__(self, entity_ref, max_slots=10):
        super().__init__(entity_ref)
        self.max_slots = max_slots
        # Wir speichern Items an Indizes. Ein Item der Größe 3 belegt Index 0, 1, 2.
        # Aber wir referenzieren das Item-Objekt nur einmal logisch.
        self.items: List[Entity] = [] 

    def add_item(self, item_entity: Entity):
        # Hier Logik einfügen, ob noch Platz auf dem Board ist (Summe der Sizes <= max_slots)
        self.items.append(item_entity)

    def get_adjacent_items(self, target_item: Entity) -> tuple[Entity | None, Entity | None]:
        # Wichtig für "When adjacent item used..."
        if target_item not in self.items:
            return None, None
        
        idx = self.items.index(target_item)
        left = self.items[idx - 1] if idx > 0 else None
        right = self.items[idx + 1] if idx < len(self.items) - 1 else None
        return left, right

    def update(self, context):
        # Leite tick update an alle Items weiter
        for item in self.items:
            item.update(context)









