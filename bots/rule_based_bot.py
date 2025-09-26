from __future__ import annotations

from typing import List, Any, Dict

from game_engine.core.card_encoding import Card
from game_engine.core.game_entities import GameState, PlayerAction
from .bot_interface import BotInterface


class RuleBasedBot(BotInterface):
    """Simple rule-based bot: play the first legal move or pass.

    Used as fallback and for auto-fill seats when testing.
    """

    def __init__(self, name: str = "RuleBot") -> None:
        self._name = name

    def choose_move(self, hand: List[Card], legal_moves: List[Any], game_state: GameState) -> Dict[str, Any]:
        if legal_moves:
            move = legal_moves[0]
            # legal_moves from engine may be Combo objects or dicts (Sam)
            if isinstance(move, dict):
                return {"type": "play_cards", "cards": move.get("cards", [])}
            else:
                return {"type": "play_cards", "cards": getattr(move, "cards", [])}
        return {"type": "pass", "cards": []}

    def get_info(self) -> Dict[str, Any]:
        return {"name": self._name, "type": "rule_base", "version": "1.0"}


