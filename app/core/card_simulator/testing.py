from data.entity import Entity
from data.component import HealthStore, TimeStore, ValueStore, ModifierStore
from data.const import StatusEffect
from data.action import Action
from data.condition import TimeCondition
from data.effect import ApplyStatusEffect

from typing import List

e = Entity()
e.add_component(HealthStore(e, 1000))
e.get_component(HealthStore).add_status_effect(StatusEffect.BURN, 5)
e.get_component(HealthStore).add_status_effect(StatusEffect.SHIELD, 10)
e.get_component(HealthStore).add_status_effect(StatusEffect.POISON, 0)
e.get_component(HealthStore).add_status_effect(StatusEffect.REGEN, 0)

# ich such die erlösung in vier wänden die ich für 400€ meine nennen darf.

class Item(Entity):
    def __init__(self, default_values:dict[str,int] | None = None, actions:List[Action] | None = None ):
        super().__init__()
        self.add_component(TimeStore(self))
        self.add_component(ModifierStore(self))
        if default_values is not None: self.add_component(ValueStore(self, default_values))
        else: self.add_component(ValueStore(self))
        if actions is not None: self.actions = actions
        self.actions: List[Action] = []


item = Item({"heal" : 10})

heal_effect = ApplyStatusEffect(StatusEffect.BURN)


use_action = Action(heal_effect, TimeCondition(3, item.get_component(TimeStore)))




context = None

print("TICKS: ", 0, "TIME", 0)
print(e)
for i in range(30):
    print("TICKS: ", i+1, "TIME", (i+1)*0.1)
    e.update(context)
    print(e)

print(e)

