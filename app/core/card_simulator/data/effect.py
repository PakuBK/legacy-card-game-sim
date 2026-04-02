from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .component import HealthComponent, StatusEffectContainer, ValueStore, ShieldComponent
from .const import StatusEffect

if TYPE_CHECKING:
    from .entity import Entity

class Effect(ABC):
    @abstractmethod
    def apply(self, source_entity: Entity, target_entity: Entity):
        ...

class DealDamageEffect(Effect):
    def __init__(self, amount_key: str = "damage"):
        """
        :param amount_key: Key in ValueStore to look up damage amount (e.g. "damage")
        """
        self.amount_key = amount_key

    def apply(self, source_entity: Entity, target_entity: Entity):
        # 1. Wert holen
        val_store = source_entity.get_component(ValueStore)
        damage_amount = val_store.get(self.amount_key) if val_store else 0

        # 2. Ziel Komponente holen
        health = target_entity.get_component(HealthComponent)
        
        # 3. Anwenden
        if health:
            health.take_damage(damage_amount, source_type="direct")

class HealEffect(Effect):
    def __init__(self, amount_key: str = "heal"):
        self.amount_key = amount_key

    def apply(self, source_entity: Entity, target_entity: Entity):
        val_store = source_entity.get_component(ValueStore)
        heal_amount = val_store.get(self.amount_key) if val_store else 0

        health = target_entity.get_component(HealthComponent)
        if health:
            health.heal(heal_amount)

class GainShieldEffect(Effect):
    def __init__(self, amount_key: str = "shield"):
        self.amount_key = amount_key

    def apply(self, source_entity: Entity, target_entity: Entity):
        val_store = source_entity.get_component(ValueStore)
        amount = val_store.get(self.amount_key) if val_store else 0

        shield = target_entity.get_component(ShieldComponent)
        if shield:
            shield.add_shield(amount)

class ApplyStatusEffect(Effect):
    """
    Applies Stacks of BURN, POISON, REGEN to target.
    """
    def __init__(self, status_type: str, amount_key: str = None):
        self.status_type = status_type
        # Wenn kein Key angegeben ist, nehmen wir den Status Namen (z.B. "poison")
        self.amount_key = amount_key if amount_key else status_type

    def apply(self, source_entity: Entity, target_entity: Entity):
        val_store = source_entity.get_component(ValueStore)
        amount = val_store.get(self.amount_key) if val_store else 0

        status_container = target_entity.get_component(StatusEffectContainer)
        if status_container:
            status_container.add_stacks(self.status_type, amount)
