from data_structures import SimpleDummy, Board


class DamageSimulator:
    def __init__(self, board, simulation_duration=60):
        self.board = board
        self.dummy = SimpleDummy()
        self.board.target = self.dummy
        self.simulation_duration = simulation_duration
        self.time = 0.0

    def simulate_step(self, delta_time=0.1):
        self.time += delta_time
        dummy = self.dummy
        dummy.current_time = self.time
        board = self.board
        board.current_time = self.time

        dummy.update_status_effects()

        for item in board.items:
            if item is None:
                continue
            if item.is_active: # ammo items needs to accounted
                item.update_status_effects(delta_time)
                effective_speed = 1.0
                if item.is_slowed():
                    effective_speed *= 0.5
                elif item.is_hasted():
                    effective_speed *= 2.0
                item.current_cooldown -= effective_speed * delta_time

                if round(item.current_cooldown, 2) <= 0:
                    item.apply_effect(dummy, self.time)


    def run_simulation(self):
        while self.time <= self.simulation_duration:
            self.simulate_step()

        burn_history = [(time, damage) for (time, damage, damage_source) in self.dummy.damage_history if damage_source=="burn"]
        poison_history = [(time, damage) for (time, damage, damage_source) in self.dummy.damage_history if
                        damage_source == "poison"]


        return {
            "total_damage": self.dummy.total_damage_taken,
            "dps": self.dummy.total_damage_taken / self.simulation_duration,
            "damage_history": self.dummy.damage_history,
            "duration" : self.simulation_duration,
            "use_counter" : self.board.use_counter,
            "crit_counter" : self.dummy.crit_counter,
            "burn_history" : burn_history,
            "poison_history" : poison_history,
            "label" : self.board.name
        }




def run_simulator_with_items(items:list, simulation_duration:int = 60, label="Board")->dict:
    """
    run the simulator with the given items in order.
    :param items: items you want to simulate, have to be in the right order.
    :return: {'damage_history', 'dps', 'total_damage'}
    """
    board = Board(name=label)
    for index, item in enumerate(items):
        board.add_item(item, position=index)
    return DamageSimulator(board, simulation_duration).run_simulation()


def run_simulator_multiple_boards(boards:list, simulation_duration:int = 60)->list:
    """
    takes multiple boards and runs the simulation with it
    :param boards: list of boards with items
    :param simulation_duration: duration of the simulation
    :return: a list of results
    """
    return [DamageSimulator(board, simulation_duration).run_simulation() for board in boards]

