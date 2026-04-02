import unittest
from app.core.card_simulator.data.entity import Entity
from app.core.card_simulator.data.component import TimeStore, ValueStore, AmmoComponent, ModifierStore
from app.core.card_simulator.data.action import Action
from app.core.card_simulator.data.condition import TimeCondition, AmmoCondition

# Mock Effect Klasse, da wir noch kein echtes Damage-System haben
class MockDamageEffect:
    def __init__(self, damage_amount):
        self.damage_amount = damage_amount
        self.trigger_count = 0
        self.last_trigger_time = 0

    def apply(self, source_entity, context):
        self.trigger_count += 1
        # Hier könnte man Context nutzen, um Damage an ein Target zu geben
        # print(f"BOOM! Dealt {self.damage_amount} damage.")


class TestItemMechanics(unittest.TestCase):
    
    def test_sword_activity(self):
        """
        Simuliert ein Item (Schwert):
        - Cooldown: 3.0 Sekunden
        - Ammo: 20 Schuss
        - Laufzeit: 30 Sekunden
        
        Erwartetes Ergebnis: Feuert genau 10 Mal (bei Sekunde 3, 6, 9 ... 30).
        """
        
        # 1. Entity Setup
        # Wir brauchen Tick Size 0.1s (Standard)
        sword = Entity(tick_size=0.1)
        
        # Components hinzufügen
        time_store = sword.add_component(TimeStore(sword))
        val_store = sword.add_component(ValueStore(sword, default_values={"cooldown": 3.0, "damage": 10}))
        ammo_comp = sword.add_component(AmmoComponent(sword, max_ammo=20))
        # ModifierStore ist wichtig, falls TimeStore update() Logik darauf zugreift
        sword.add_component(ModifierStore(sword))

        # 2. Logic Setup (Conditions, Costs, Effects)
        
        # Conditions
        cond_time = TimeCondition(cooldown_key="cooldown", time_store=time_store, value_store=val_store)
        cond_ammo = AmmoCondition(ammo_component=ammo_comp)
        
        # Costs (Wrapper Functions)
        def pay_time_cost():
            # Wichtig: Hole den aktuellen Cooldown Wert (könnte sich ja geändert haben)
            cd = val_store.get("cooldown")
            time_store.reduce_progress(cd)
            
        def pay_ammo_cost():
            ammo_comp.try_consume()
            
        # Effect
        damage_effect = MockDamageEffect(damage_amount=10)
        
        # Action zusammenbauen
        attack_action = Action(
            entity_ref=sword,
            conditions=[cond_time, cond_ammo],
            costs=[pay_time_cost, pay_ammo_cost],
            effects=[damage_effect]
        )
        
        sword.add_action(attack_action)

        # 3. Simulation Loop (30 Sekunden)
        sim_duration = 30.0
        ticks = int(sim_duration / sword.tick_size) # 300 Ticks
        
        for i in range(1, ticks + 1):
            sword.update(context=None)
            
            # Optional: Debug Print alle Sekunde
            # if i % 10 == 0:
            #     print(f"Time: {i*0.1:.1f}s | Progress: {time_store.progress_in_seconds:.1f}s | Triggers: {damage_effect.trigger_count}")

        # 4. Assertions
        
        # Sollte genau 10 mal gefeuert haben (30s / 3s = 10)
        self.assertEqual(damage_effect.trigger_count, 10, "Item should have triggered exactly 10 times.")
        
        # Sollte 10 Munition verbraucht haben (20 Start - 10 Schuss = 10 Rest)
        self.assertEqual(ammo_comp.current_ammo, 10, "Ammo count should be reduced by 10.")
        
        # Der Time Progress sollte am Ende der Simulation wieder bei fast 0 sein 
        # (da er exakt bei Sekunde 30 gefeuert hat)
        # Hinweis: Wegen Floating Point Ungenauigkeit nutzen wir assertAlmostEqual
        self.assertAlmostEqual(time_store.progress_in_seconds, 0.0, delta=0.001, msg="Progress should be reset after firing at the very last tick.")

    def test_ammo_depletion(self):
        """
        Testet, dass das Item aufhört zu feuern, wenn Ammo alle ist.
        - Cooldown: 1.0 Sekunde
        - Ammo: 3 Schuss
        - Laufzeit: 10 Sekunden
        
        Erwartung: Feuert nur 3 Mal, danach lädt Zeit auf, aber Action blockiert.
        """
        sword = Entity(tick_size=0.1)
        time_store = sword.add_component(TimeStore(sword))
        val_store = sword.add_component(ValueStore(sword, default_values={"cooldown": 1.0}))
        ammo_comp = sword.add_component(AmmoComponent(sword, max_ammo=3))
        sword.add_component(ModifierStore(sword))

        cond_time = TimeCondition("cooldown", time_store, val_store)
        cond_ammo = AmmoCondition(ammo_comp)
        
        mock_effect = MockDamageEffect(0)
        
        # Action mit Kosten: Zeit abziehen UND Ammo verbrauchen
        action = Action(
            entity_ref=sword,
            conditions=[cond_time, cond_ammo], 
            costs=[lambda: time_store.reduce_progress(1.0), lambda: ammo_comp.try_consume()],
            effects=[mock_effect]
        )
        sword.add_action(action)

        # Simuliere 10 Sekunden (sollte 10 mal feuern KÖNNEN von der Zeit her, aber Ammo limitiert auf 3)
        # 10s / 0.1s = 100 Ticks
        for _ in range(100):
            sword.update(None)

        self.assertEqual(mock_effect.trigger_count, 3, "Should stop firing after ammo is depleted.")
        self.assertEqual(ammo_comp.current_ammo, 0)
        
        # Der Progress sollte weitergelaufen sein ("Overcharge"), da wir time nicht resetten,
        # wenn wir nicht feuern (Action wird abgelehnt, weil AmmoCondition False ist).
        # Nach 10 Sekunden:
        # 3 Sekunden wurden "bezahlt" für die 3 Schüsse.
        # 7 Sekunden sind seitdem vergangen und stauen sich an.
        self.assertAlmostEqual(time_store.progress_in_seconds, 7.0, delta=0.1)

if __name__ == "__main__":
    unittest.main()