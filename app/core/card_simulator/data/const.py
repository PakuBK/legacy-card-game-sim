from typing import Literal

# TARGETS
PLAYER = "player"
ENEMY = "enemy"
RDM_PLAYER = "random_player"
ITEM = "item"




StatusEffect = Literal["poison", "burn", "regeneration", "shield"]
InstantEffect = Literal["damage", "heal"]