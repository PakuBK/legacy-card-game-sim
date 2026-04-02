import pytest

from app.core.card_simulator.data.component import HealthComponent, ShieldComponent, StatusEffectContainer
from app.core.card_simulator.data.entity import Entity

def test_initial_health():
    entity = Entity()
    health_comp = entity.add_component(HealthComponent(entity_ref=entity, init_max_health=1000))
    assert health_comp.current_health == 1000

def test_apply_damage_and_heal_without_shield():
    entity = Entity()
    health_comp = entity.add_component(HealthComponent(entity_ref=entity, init_max_health=100))

    # Ohne ShieldComponent sollte Schaden direkt auf HP gehen
    health_comp.take_damage(30)
    assert health_comp.current_health == 70

    health_comp.heal(20)
    assert health_comp.current_health == 90

    # Heilung darf Max-Health nicht überschreiten
    health_comp.heal(50)
    assert health_comp.current_health == 100

def test_shield_mechanics():
    """
    Testet, dass normales Schild vor normalem Schaden schützt.
    """
    entity = Entity()
    health_comp = entity.add_component(HealthComponent(entity, init_max_health=100))
    shield_comp = entity.add_component(ShieldComponent(entity))

    shield_comp.add_shield(20)
    
    # 1. Schaden kleiner als Schild
    health_comp.take_damage(10)
    assert shield_comp.value == 10
    assert health_comp.current_health == 100 # Kein HP Verlust

    # 2. Schaden größer als restliches Schild
    health_comp.take_damage(20) # 10 Schild sind noch da
    assert shield_comp.value == 0
    assert health_comp.current_health == 90 # 10 Damage gingen durch

def test_burn_status_reduces_health():
    # Burn Interval ist 0.5s. Wir setzen Tick Size auf 0.5 damit 1 Tick = 1 Trigger
    entity = Entity(tick_size=0.5) 
    
    health_comp = entity.add_component(HealthComponent(entity, init_max_health=10))
    status_comp = entity.add_component(StatusEffectContainer(entity))

    # Burn mit Wert 2 hinzufügen (Stacks)
    status_comp.add_stacks("burn", 2)

    # update calls status_comp.update -> check timers -> calls health_comp.take_damage
    status_comp.update({})
    
    assert health_comp.current_health == 8  # 10 - 2 Schaden
    assert status_comp.get_stacks("burn") == 1  # Burn-Wert reduziert sich um 1 nach Trigger (Decay)

def test_poison_ignores_shield():
    # Poison Interval ist 1.0s.
    entity = Entity(tick_size=1.0)
    
    health_comp = entity.add_component(HealthComponent(entity, init_max_health=10))
    shield_comp = entity.add_component(ShieldComponent(entity))
    status_comp = entity.add_component(StatusEffectContainer(entity))

    # Poison für 3 Schaden
    status_comp.add_stacks("poison", 3)
    # Shield für 5
    shield_comp.add_shield(5)

    # Trigger Poison Update
    status_comp.update({})

    # Poison ignoriert Shield ("piercing" damage type in config)
    assert health_comp.current_health == 7
    # Shield sollte unberührt bleiben
    assert shield_comp.value == 5
    # Poison decay ist False, Stacks sollten gleich bleiben
    assert status_comp.get_stacks("poison") == 3