# The Bazaar Simulator - Architecture & Status

This project simulates the combat mechanics of "The Bazaar" using an ECS-like (Entity Component System) approach. The goal is a modular, extensible, and performant simulation that can be used to test tactics.

## 1. Core Architecture

The codebase follows a composition-over-inheritance approach. There are no fixed classes for "sword" or "wand". Everything is an entity defined by its components.

### The Building Blocks

1. **Entity (`entity.py`)**
    - A generic container with an ID and a list of components.
    - Has a `tick_size` (for example 0.1s) for deterministic time simulation.

2. **Components (`component.py`)**
    - Hold data and specific logic as smart components.
    - Split responsibilities cleanly:
        - Vitality (player): `HealthComponent`, `ShieldComponent`, `StatusEffectContainer` (manages burn and poison ticks).
        - Item logic: `TimeStore` (cooldown progress), `ValueStore` (stats such as damage), `ModifierStore` (buffs and debuffs), `AmmoComponent`.
        - Meta: `TagComponent` (weapon, magic), `ItemSize` (small, medium).

3. **Action System (Transactional)**
    - Items do not fire randomly. The project uses a strict condition-cost-effect model:
        - Conditions (`condition.py`): stateless checks such as "Is the cooldown ready?" and "Is ammo available?".
        - Costs: if conditions pass, spend the required resources, for example "remove 1 ammo" or "reset the cooldown timer".
        - Effects (`effect.py`): after payment, apply the result, for example "deal damage to the enemy".
    - This enables more complex logic, such as an item charging up but not firing because ammo is missing.

4. **Status Effects**
    - Centralized in `StatusEffectContainer`.
    - Automatically distinguishes effect types:
        - Burn: damage plus decay over time.
        - Poison: piercing damage that ignores shield, with no decay.
        - Freeze: implemented in `ModifierStore` as a multiplier of `0.0`.

---

## 2. Data Model Examples

What does an object look like in this system?

**The player (entity):**

```python
Entity(
    components=[
        HealthComponent(max=1000),
        ShieldComponent(),          # Separate because poison ignores it
        StatusEffectContainer(),    # Manages burn and poison timers
        BoardComponent()            # TODO: holds the items
    ]
)
```

**An item (for example an ice sword):**

```python
Entity(
    components=[
        TimeStore(),                # Progress bar
        ValueStore(cooldown=3.0, damage=10),
        TagComponent(["Weapon", "Ice"]),
        ModifierStore()             # Can receive haste, slow, or freeze
    ],
    actions=[
        Action(
            conditions=[TimeCondition, AmmoCondition],
            costs=[ResetTime, ConsumeAmmo],
            effects=[DealDamageEffect]
        )
    ]
)
```

---

## 3. Progress Checklist

Current implementation status based on the game rules.

### Implemented and Tested

- Entity foundation and component system.
- HP and healing with max-HP logic.
- Shield mechanics that absorb damage before HP.
- Status effect basics:
    - Burn: damage over time, self-decaying.
    - Poison: damage over time, ignores shield, no decay.
    - Regeneration: healing over time.
- Cooldown mechanics:
    - Time-based charging.
    - Haste and slow via `ModifierStore`.
    - Freeze that stops time flow completely.
- Resources: `AmmoComponent`.
- Action triggering only when all conditions are satisfied (time plus ammo).

### In Progress / TODO

- Board logic for `BoardComponent`.
- Positioning and adjacency:
    - Items need to know which items are left and right of them.
    - Effects such as "items adjacent to this heal for 5".
- Event bus / reactivity:
    - Support for effects like "when you use an item...".
    - Items need to listen for events using an observer pattern.
- Sandstorm: the global timer that scales damage upward.
- Game loop: the combat loop that ticks two player entities against each other.
- Item loader: parsing JSON or database data into the entity structure.
