# Bazaar Simulator Backend

This repository contains a FastAPI backend and a card-combat simulation prototype inspired by The Bazaar. The project is structured around an ECS-like model: game objects are entities composed from components, and combat behavior is driven by conditions, costs, and effects rather than hard-coded item classes.

## What This Repo Is For

The main goal is to simulate item-based combat in a deterministic way so item builds, cooldown timings, status effects, and resource interactions can be tested quickly. The current codebase reflects two layers of the same idea:

- A newer ECS-style implementation under `app/core/card_simulator/data/` and `app/core/card_simulator/simulator/`.
- A legacy/compatibility simulator path in `app/core/card_simulator/card_simulator.py` and `app/core/card_simulator/data_structures.py`.

## High-Level Design

- `Entity` is the container object.
- `Component` instances store state and update their own behavior.
- `Action` objects use a `condition -> cost -> effect` flow.
- Status effects such as burn, poison, regeneration, haste, slow, and freeze are modeled explicitly.
- The simulation is intended to run with a fixed tick size for deterministic results.

## Current Backend Surface

- `app/main.py` creates the FastAPI application.
- `app/api/routes.py` exposes a basic root route under `/api/v1/`.
- The simulator logic lives in `app/core/card_simulator/`.
- The existing tests cover health, shields, burn, poison, and item cooldown behavior.

## Key Files

- `app/main.py`: FastAPI entry point.
- `app/api/routes.py`: API router and root health-style response.
- `app/core/card_simulator/data/entity.py`: Entity container and component handling.
- `app/core/card_simulator/data/component.py`: Core component types such as health, shield, status effects, cooldown, ammo, and modifiers.
- `app/core/card_simulator/data/action.py`: Action orchestration.
- `app/core/card_simulator/data/condition.py`: Trigger conditions.
- `app/core/card_simulator/data/effect.py`: Combat and utility effects.
- `app/core/card_simulator/simulator/simulator_engine.py`: Simulator entry point for the ECS-style engine.
- `app/core/card_simulator/card_simulator.py`: Legacy board-based simulator.

## Status Snapshot

Implemented and covered by tests:

- Entity and component foundation.
- Health and healing.
- Shield handling.
- Burn, poison, and regeneration status effects.
- Cooldown progression with haste, slow, and freeze behavior.
- Ammo handling.
- Action triggering when time and ammo conditions are satisfied.

Planned next steps:

- Board logic for holding items.
- Positioning and adjacency rules.
- Event bus / observer-style reactions.
- Sandstorm global scaling timer.
- A full combat loop between two player entities.
- Data loading from JSON or a database into the entity model.

## Tests

The repository already includes unit tests under `tests/` that validate the current health and item simulation behavior. Use them as the source of truth for the existing runtime contract.
