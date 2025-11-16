"""
Bot interface for Phase 3 (backend rooms with AI seats).

This interface is intentionally placed in ai_common so it can be reused by
any backend service without coupling to a particular web framework.

Contract:
- choose_move(hand, game_state) -> {"type": "play_cards"|"pass", "cards": [Card]}
- get_info() -> metadata for logging/debugging {name, type, version}
"""

from __future__ import annotations

from typing import List, Tuple, Optional, Dict, Any

from game_engine.core.card_encoding import Card
from game_engine.core.game_entities import GameState


class BotInterface:
    """Abstract bot interface."""

    def choose_move(
        self,
        hand: List[Card],
        game_state: GameState,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def get_info(self) -> Dict[str, Any]:
        return {"name": "unknown", "type": "bot", "version": "0"}


