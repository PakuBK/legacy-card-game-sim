from card_simulator import *
from random import random

def print_details(results:list):
    for result in results:

        total_burn_damage = 0
        for (time, damage) in result['burn_history']:
            total_burn_damage += damage

        total_poison_damage = 0
        for (time, damage) in result['poison_history']:
            total_poison_damage += damage


        print(f"Stats for {result['label']}")
        for (label, value) in result['use_counter'].items():
            print(f"{label} x {value}")
        print("crits: ", result['crit_counter'])
        print("total burn", total_burn_damage)
        print("total poison", total_poison_damage)
        print("---")
        print(f"DPS: {result['dps']}")
        print("---") #125-144

if __name__ == '__main__':
    def flat_damage_effect(item: Item, target: SimpleDummy, current_time: float):
        crit_mult = 2 if random() < item.crit_chance else 1

        if crit_mult == 2:
            target.crit_counter += 1

        target.take_damage(item.damage * crit_mult, item.name)

    def flat_damage_and_burn(item: Item, target: SimpleDummy, current_time):
        crit_mult = 2 if random() < item.crit_chance else 1

        if crit_mult == 2:
            target.crit_counter += 1

        target.take_damage(item.damage * crit_mult, item.name)
        target.apply_burn_effect(item.burn)


    def burn_effect(item: Item, target: SimpleDummy, current_time):
        target.apply_burn_effect(item.burn)


    def poison_effect(item: Item, target: SimpleDummy, current_time):
        target.apply_poison_effect(item.poison)


    def slow_effect(item: Item, target: SimpleDummy, current_time):
        item.board.trigger(Trigger.SLOW)
        item.board.trigger(Trigger.SLOW)


    def haste_effect(item: Item, duration):
        item.add_status_effect('haste', duration)


    def haste_all_items_effect(item: Item, target: SimpleDummy, current_time):
        item.board.give_effect_on_all_items(haste_effect, 2)


    def charge_effect(item: Item):
        item.charge(2)

    def reload_right_item(item: Item, target: SimpleDummy, current_time):
        right = item.board.get_item_to_the_right(item.position)
        print(right.name)
        if right is None:
            return
        right.reload(2)

    def haste_on_start_passive(item: Item, target: SimpleDummy, current_time):
        item.board.give_effect_on_all_size_items(haste_effect, 1, "small")

    def buff_damage_right(item: Item, target: SimpleDummy, current_time):
        right = item.board.get_item_to_the_right(item.position)
        if right is None:
            return
        right.buff_damage(item.damage)





    Revolver_1 = Item("Revolver", "small", "Weapon", is_active=True, cooldown=2.1, damage=112, burn=12,
                      crit_chance=1, on_use=flat_damage_and_burn)

    Holster = Item("Holster", "small", "Tool", is_active=False,
                   on_start=haste_on_start_passive)

    Buffer = Item("Buffer", "small", "Tool", is_active=True, cooldown=4.0, damage=16, on_use=buff_damage_right)


    Revolver_2 = Item("Revolver", "small", "Weapon", is_active=True, cooldown=2.1, damage=112, burn=12,
                      crit_chance=1, on_use=flat_damage_and_burn)

    Pop_Snappers = Item("Pop_Snappers", "small", "Tool", is_active=True, cooldown=3, burn=6, ammo=3,
                        on_use=burn_effect)

    Board1 = Board(name="Haste")
    Board1.add_item(Buffer, 0)
    Board1.add_item(Revolver_1, 1)
    Board1.add_item(Holster, 2)

    Board2 = Board(name="Burn")
    Board2.add_item(Buffer, 0)
    Board2.add_item(Holster, 2)
    Board2.add_item(Revolver_2, 1)
    Board2.add_item(Pop_Snappers, 3)

    # deep copy items todo



    results = run_simulator_multiple_boards([Board1, Board2], simulation_duration=30)

    print_details(results)


    plot_multiple_results(results)

