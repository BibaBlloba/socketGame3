from dataclasses import dataclass
from typing import Dict


@dataclass
class Player:
    name: str
    x: int
    y: int


class PlayerMagager:
    def __init__(self) -> None:
        self.player_list: Dict[str, Player] = {}

    def add_player(self, name: str, x: int, y: int):
        self.players[name] = Player(name, x, y)
