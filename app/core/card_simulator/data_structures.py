from enum import Enum

class ItemStatusEffect(Enum):
    HASTE = 0

class Trigger(Enum):
    USE_ADJACENT = 0
    SLOW = 1
    HASTE = 2
    USE = 3

class Item:
    def __init__(self, name, size, tags, is_active=False, cooldown=0, damage=0, burn=0, poison=0, heal=0, shield=0, ammo=None,
                 on_use=None, on_start=None,triggers=None, on_trigger=None, multicast=1, crit_chance=0):
        self.name = name
        self.tags = tags
        self.size = size
        self.is_active = is_active
        self.base_cooldown = cooldown
        self.current_cooldown = cooldown
        self.damage = damage
        self.heal = heal
        self.shield = shield
        self.burn = burn
        self.poison = poison
        self.crit_chance = crit_chance
        self.multicast = multicast
        self.max_ammo = ammo
        self.current_ammo = ammo
        self.on_use = on_use
        self.on_start = on_start
        self.status_effects = {'haste': 0, 'slow': 0, 'freeze': 0} # eig. nur haste // slow, freeze irrelevant für sim
        self.triggers = [] if triggers is None else triggers
        self.on_trigger = on_trigger

        self.board: Board = None
        self.position = None


    def has_tag(self, tag) -> bool:
        for item_tag in self.tags:
            if tag is item_tag:
                return True
        return False

    def reset_cooldown(self):
        self.current_cooldown = self.base_cooldown

    def charge(self, value):
        c_cd = self.current_cooldown
        if c_cd - value < 0:
            self.apply_effect(self.board.target, self.board.current_time)
            remainder = value - c_cd
            self.current_cooldown = self.base_cooldown - remainder
        else:
            self.current_cooldown = max(c_cd-value, 0)

    def reload(self, amount):
        self.current_ammo += amount

    def apply_effect(self, target, current_time):
        if self.on_use:
            if self.max_ammo is not None:
                if self.current_ammo > 0:
                    self.current_ammo -= 1
                else: # ammo is empty
                    return

            for _ in range(self.multicast):
                self.on_use(self, target, current_time)
                self.board.register_use(self.name)
                # use trigger
                self.board.trigger(Trigger.USE)
                self.board.adjacent_trigger(Trigger.USE_ADJACENT, self.position)


            self.reset_cooldown()

    def add_status_effect(self, effect: str, duration):
        self.status_effects[effect] = duration

    def update_status_effects(self, delta_time):
        for (effect, duration) in self.status_effects.items():
            if duration > 0:
                self.status_effects[effect] = duration - delta_time
            else:
                self.status_effects[effect] = 0

    def buff_damage(self, value):
        self.damage += value

    def is_hasted(self):
        return self.status_effects['haste'] > 0

    def is_slowed(self):
        return self.status_effects['slow'] > 0


class Board:
    def __init__(self, name="Board"):
        self.items = [None] * 10
        self.target = None
        self.current_time = 0
        self.name = name
        self.use_counter = {}

    def add_item(self, item, position):
        if position >= len(self.items):
            return
        item.board = self
        item.position = position
        self.items[position] = item

    def get_item_to_the_left(self, position) -> Item:
        if position-1 < 0:
            return None
        return self.items[position-1]

    def get_item_to_the_right(self, position) -> Item:
        if position+1 >= len(self.items):
            return None
        return self.items[position+1]

    def trigger(self, effect:Trigger):
        for item in self.items:
            if item is None:
                continue
            if effect in item.triggers:
                item.on_trigger(item)

    def adjacent_trigger(self, effect:Trigger, position):
        left = self.get_item_to_the_left(position)
        right = self.get_item_to_the_right(position)
        if left is not None and effect in left.triggers:
            left.on_trigger(left)
        if right is not None and effect in right.triggers:
            right.on_trigger(right)


    def give_effect_on_all_items(self, effect, duration):
        for item in self.items:
            if item is None:
                continue
            effect(item, duration)


    def give_effect_on_all_size_items(self, effect, duration, size):
        for item in self.items:
            if item is None:
                continue
            if item.size is "small":
                effect(item, duration)



    def register_use(self, name:str):
        if name in self.use_counter:
            self.use_counter[name] += 1
        else:
            self.use_counter[name] = 1



class SimpleDummy:
    def __init__(self):
        self.total_damage_taken = 0
        self.status_effects = {'burn': (0,0), 'poison': (0,0)} # type : [value, last_tick]
        self.damage_history = [] # (time, damage, damage_source)
        self.current_time = 0
        self.crit_counter = 0

    def take_damage(self, damage, damage_source=None):
        self.total_damage_taken += damage
        self.damage_history.append((self.current_time, damage, damage_source))


    def apply_burn_effect(self, value):
        current_burn, last_tick = self.status_effects['burn']
        if current_burn == 0:
            last_tick = self.current_time
        self.status_effects['burn'] = (current_burn+value, last_tick)

    def apply_poison_effect(self, value):
        current_poison, last_tick = self.status_effects['poison']
        if current_poison == 0:
            last_tick = self.current_time
        self.status_effects['poison'] = (current_poison+value, last_tick)

    def update_status_effects(self):
        # burn
        current_time = self.current_time
        current_burn, last_burn_tick = self.status_effects['burn']
        if current_burn > 0 and round(current_time - last_burn_tick, 2) >= 0.5:
            self.take_damage(current_burn, damage_source="burn")
            self.status_effects['burn'] = (current_burn - 1, current_time)
        # poison
        current_poison, last_poison_tick = self.status_effects['poison']
        if current_poison > 0 and round(current_time - last_poison_tick, 2) >= 1.0:
            self.take_damage(current_poison, damage_source="poison")
            self.status_effects['poison'] = (current_poison, current_time)