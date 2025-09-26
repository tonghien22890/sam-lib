from __future__ import annotations

from typing import List, Dict, Any, Optional
import os
import joblib

from ai_common.bots.model_bot import ModelProvider
from ai_common.adapters.bot_adapter import GeneralAdapter


class GeneralPlayProvider(ModelProvider):
    """General gameplay provider using per-candidate rank-only model.

    Loads `model_build/models/optimized_general_model_v3.pkl` and uses the
    Stage 1 per-candidate classifier to select the best legal move.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        super().__init__(name="general_play", version="v3")
        self._adapter = GeneralAdapter(model_path=model_path)

    def _ensure_loaded(self):
        return self._adapter.ensure_ready()

    def predict(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return the best move from legal_moves based on model probability.

        Expects game_record to contain at least: 'hand', 'cards_left', and 'meta.legal_moves'.
        """
        if not self._adapter.ensure_ready():
            for m in legal_moves:
                if m.get("type") == "play_cards" and m.get("cards"):
                    return {"type": "play_cards", "cards": m.get("cards")}
            return {"type": "pass", "cards": []}

        # Debug print top candidates is handled within adapter if needed; here keep simple
        return self._adapter.predict(game_record, legal_moves)


