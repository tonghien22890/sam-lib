from __future__ import annotations

from typing import List, Any, Dict, Optional
import time
import os

from game_engine.core.card_encoding import Card, CardEncoder
from game_engine.core.game_entities import GameState
from .bot_interface import BotInterface
from ai_common.model_providers.production_bao_sam_provider import get_production_bao_sam_provider
from ai_common.adapters.unbeatable_adapter import UnbeatableAdapter


class ModelProvider:
    """Abstracts how we call an ML model (local/in-process or HTTP)."""

    def __init__(self, name: str = "model", version: str = "0") -> None:
        self.name = name
        self.version = version

    def predict(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return action dict {type, cards[]}.
        Default naively picks the first legal move.
        """
        for m in legal_moves:
            if m.get("type") == "play_cards" and m.get("cards"):
                return {"type": "play_cards", "cards": m.get("cards")}
        return {"type": "pass", "cards": []}


class ModelBot(BotInterface):
    """Bot backed by a model provider.

    provider.predict expects encoded state similar to BaseGame.get_game_record().
    """

    def __init__(self, provider: Optional[ModelProvider] = None) -> None:
        self.provider = provider or ModelProvider()
        self._last_latency_ms: Optional[int] = None
        self.unbeatable_adapter = UnbeatableAdapter()
        
        # Two-Layer Architecture for general gameplay
        try:
            from ai_common.adapters.two_layer_adapter import TwoLayerAdapter
            # Try to load trained model if available
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "model_build", "models", "style_learner_model.pkl")
            self.two_layer_adapter = TwoLayerAdapter(model_path)
        except ImportError:
            print("⚠️ TwoLayerAdapter not available, using fallback")
            self.two_layer_adapter = None

    def choose_move(self, hand: List[Card], legal_moves: List[Any], game_state: GameState) -> Dict[str, Any]:
        # Build game_record-like minimal view
        last_move = game_state.last_move
        game_record: Dict[str, Any] = {
            "game_id": game_state.game_id,
            "game_type": game_state.game_type.value,
            "round_id": game_state.round_id,
            "turn_id": game_state.turn_id,
            "player_id": game_state.current_player_id,
            "hand": CardEncoder.encode_hand(hand),
            "last_move": {
                "player_id": last_move.player_id,
                "cards": CardEncoder.encode_hand(last_move.cards),
                "combo_type": last_move.combo.combo_type.value if last_move and last_move.combo else None,
                "rank_value": last_move.combo.rank_value if last_move and last_move.combo else None,
            } if last_move else None,
            "players_left": game_state.get_players_left(),
            "cards_left": game_state.cards_left.copy(),
        }

        # Normalize legal_moves
        lm: List[Dict[str, Any]] = []
        for m in legal_moves:
            if isinstance(m, dict):
                lm.append({
                    "type": m.get("type", "play_cards"),
                    "cards": m.get("cards", []),
                    "combo_type": m.get("combo_type"),
                    "rank_value": m.get("rank_value"),
                })
            else:
                lm.append({
                    "type": "play_cards",
                    "cards": [c.card_id for c in getattr(m, "cards", [])],
                    "combo_type": getattr(getattr(m, "combo", None), "combo_type", None).value if getattr(m, "combo", None) else None,
                    "rank_value": getattr(getattr(m, "combo", None), "rank_value", None),
                })

        # If Sam and at opening (round 0 turn 0 no last_move), try Báo Sâm first
        if game_state.game_type.value == "sam" and game_state.round_id == 0 and game_state.turn_id == 0 and game_state.last_move is None:
            try:
                bao_provider = get_production_bao_sam_provider()
                bs = bao_provider.predict_bao_sam_decision(game_record.get("hand", []), [])
                if bs.get("should_declare"):
                    for m in lm:
                        if m.get("type") == "declare_bao_sam":
                            return m
            except Exception:
                pass

        # Check if this is a Báo Sâm bot that should use ordered sequence
        if self._should_use_ordered_sequence(game_state, lm):
            action = self._choose_move_with_ordered_sequence(hand, lm, game_state)
        else:
            # Use Two-Layer Architecture for general gameplay
            if self.two_layer_adapter is not None:
                print(f"🤖 [TwoLayer] Using Two-Layer Architecture for {game_state.game_type.value} game")
                start = time.perf_counter()
                action = self.two_layer_adapter.predict(game_record, lm)
                self._last_latency_ms = int((time.perf_counter() - start) * 1000)
                print(f"🤖 [TwoLayer] Predicted action: {action}")
            else:
                # Fallback to original provider
                print(f"🤖 [Fallback] Using original provider for {game_state.game_type.value} game")
                start = time.perf_counter()
                action = self.provider.predict(game_record, lm)
                self._last_latency_ms = int((time.perf_counter() - start) * 1000)
        
        return action
    
    def _should_use_ordered_sequence(self, game_state: GameState, legal_moves: List[Dict[str, Any]]) -> bool:
        """Check if bot should use ordered sequence (Báo Sâm scenario)"""
        # Check if this is Sam game and bot has declared Báo Sâm
        if game_state.game_type.value != "sam":
            return False
            
        # Check if there are play_cards moves available (not just pass/declare)
        has_play_moves = any(m.get("type") == "play_cards" for m in legal_moves)
        if not has_play_moves:
            return False
            
        # Only use ordered sequence when bot has declared Báo Sâm
        # For now, use Two-Layer Architecture for all Sam gameplay to learn strategy
        # TODO: Add logic to detect if this bot declared Báo Sâm
        return False
    
    def _choose_move_with_ordered_sequence(self, hand: List[Card], legal_moves: List[Dict[str, Any]], game_state: GameState) -> Dict[str, Any]:
        """Choose move using ordered sequence from UnbeatableAdapter"""
        try:
            # Get hand as card IDs
            hand_ids = [c.card_id for c in hand]
            
            # Get ordered sequence
            sequence_result = self.unbeatable_adapter.get_ordered_sequence(
                hand_ids, 
                len(game_state.players), 
                "bao_sam_optimal"
            )
            
            ordered_sequence = sequence_result.get('sequence', [])
            print(f"🤖 [SequenceOrder] Bot using ordered sequence: {len(ordered_sequence)} combos")
            
            # Find the first combo from ordered sequence that matches available legal moves
            for combo in ordered_sequence:
                combo_cards = combo.get('cards', [])
                combo_type = combo.get('combo_type')
                rank_value = combo.get('rank_value')
                
                # Find matching legal move
                for move in legal_moves:
                    if (move.get('type') == 'play_cards' and 
                        set(move.get('cards', [])) == set(combo_cards) and
                        move.get('combo_type') == combo_type and
                        move.get('rank_value') == rank_value):
                        
                        print(f"🤖 [SequenceOrder] Bot chose combo: {combo_type} rank={rank_value} cards={combo_cards}")
                        return move
            
            # Fallback: use first available legal move
            for move in legal_moves:
                if move.get('type') == 'play_cards':
                    print(f"🤖 [SequenceOrder] Fallback to first legal move: {move}")
                    return move
                    
            # Last resort: pass
            print(f"🤖 [SequenceOrder] No moves available, passing")
            return {"type": "pass", "cards": []}
            
        except Exception as e:
            print(f"🤖 [SequenceOrder] Error using ordered sequence: {e}")
            # Fallback to normal prediction
            game_record = {
                "game_id": game_state.game_id,
                "game_type": game_state.game_type.value,
                "round_id": game_state.round_id,
                "turn_id": game_state.turn_id,
                "player_id": game_state.current_player_id,
                "hand": [c.card_id for c in hand],
                "last_move": None,
                "players_left": game_state.get_players_left(),
                "cards_left": game_state.cards_left.copy(),
            }
            return self.provider.predict(game_record, legal_moves)

    def get_info(self) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            "name": self.provider.name,
            "type": "model",
            "version": self.provider.version,
        }
        if self._last_latency_ms is not None:
            meta["latencyMs"] = self._last_latency_ms
        return meta


