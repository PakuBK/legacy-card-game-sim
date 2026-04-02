from app.core.card_simulator.data.component import Component
from app.core.card_simulator.data.entity import Entity
from app.core.card_simulator.data.component import ComponentSpace


class Simulator():
    def __init__(self):
        ...

    def run_simulation(self, duration:int=30, tick_size: float = 0.1, ) -> None:
        board = Entity(tick_size=tick_size)
        space = board.add_component(ComponentSpace(board, 10))
        space._place_component()
