"""
Enhanced Model Provider

This module provides an enhanced model provider that integrates both general game models
and Báo Sâm specialized models for intelligent AI decision making.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add model_build to path
sys.path.append(str(Path(__file__).parent.parent / "model_build"))

try:
    from model_build.core.inference import predict as predict_general
    from .bao_sam_model_provider import get_bao_sam_provider
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    print("⚠️  Models not available. Install model_build dependencies.")

class EnhancedModelProvider:
    """Enhanced model provider that combines general and Báo Sâm models"""
    
    def __init__(self, models_dir: str = "model_build/runs"):
        self.models_dir = models_dir
        self.general_model_path = os.path.join(models_dir, "phase4_rf.pkl")
        self.bao_sam_provider = get_bao_sam_provider() if MODELS_AVAILABLE else None
        self.models_loaded = False
        
        if MODELS_AVAILABLE:
            self._check_models()
    
    def _check_models(self):
        """Check if models are available"""
        general_available = os.path.exists(self.general_model_path)
        bao_sam_available = self.bao_sam_provider and self.bao_sam_provider.is_available()
        
        self.models_loaded = general_available or bao_sam_available
        
        if general_available:
            print(f"✅ General game model available: {self.general_model_path}")
        else:
            print(f"⚠️  General game model not found: {self.general_model_path}")
        
        if bao_sam_available:
            print("✅ Báo Sâm models available")
        else:
            print("⚠️  Báo Sâm models not available")
    
    def predict(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced prediction using both general and Báo Sâm models"""
        
        # Check if we're in a Báo Sâm scenario
        sam_state = game_record.get("sam_state", {})
        is_bao_sam = sam_state.get("is_bao_sam", False)
        is_bao_sam_player = sam_state.get("is_bao_sam_player", False)
        
        # If Báo Sâm is active and we have Báo Sâm models, use specialized logic
        if is_bao_sam and self.bao_sam_provider and self.bao_sam_provider.is_available():
            return self._predict_bao_sam_scenario(game_record, legal_moves, is_bao_sam_player)
        
        # Otherwise, use general model or fallback
        if os.path.exists(self.general_model_path):
            try:
                return predict_general(self.general_model_path, game_record)
            except Exception as e:
                print(f"❌ Error with general model prediction: {e}")
        
        # Fallback to first legal move
        return self._fallback_prediction(legal_moves)
    
    def _predict_bao_sam_scenario(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]], 
                                 is_bao_sam_player: bool) -> Dict[str, Any]:
        """Predict for Báo Sâm scenarios"""
        
        if is_bao_sam_player:
            # Báo Sâm declarer should play aggressively
            print("🎯 Báo Sâm declarer: playing aggressively")
            
            # Use combo sequence model if available
            if self.bao_sam_provider.combo_model:
                hand = game_record.get("hand", [])
                # Find current combo sequence position
                sequence_position = len(game_record.get("sammove_sequence", []))
                
                # Predict next optimal combo
                next_combo = self.bao_sam_provider.predict_next_combo(hand, {}, sequence_position)
                if next_combo and next_combo.get("cards"):
                    # Find matching legal move
                    for move in legal_moves:
                        if move.get("cards") == next_combo.get("cards"):
                            return {"type": "play_cards", "cards": move.get("cards")}
            
            # Fallback: play highest rank card
            return self._play_highest_rank(legal_moves)
        
        else:
            # Other players should try to block Báo Sâm declarer
            print("🛡️  Non-declarer: trying to block Báo Sâm")
            
            # Try to play cards that can block
            return self._try_to_block(legal_moves)
    
    def _play_highest_rank(self, legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Play the highest rank card available"""
        play_moves = [m for m in legal_moves if m.get("type") == "play_cards" and m.get("cards")]
        
        if not play_moves:
            return {"type": "pass", "cards": []}
        
        # Sort by rank value (higher is better)
        play_moves.sort(key=lambda m: m.get("rank_value", 0), reverse=True)
        return {"type": "play_cards", "cards": play_moves[0].get("cards")}
    
    def _try_to_block(self, legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Try to block Báo Sâm declarer"""
        play_moves = [m for m in legal_moves if m.get("type") == "play_cards" and m.get("cards")]
        
        if not play_moves:
            return {"type": "pass", "cards": []}
        
        # For blocking, play any valid move (strategy can be enhanced)
        return {"type": "play_cards", "cards": play_moves[0].get("cards")}
    
    def _fallback_prediction(self, legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback prediction when no models are available"""
        for m in legal_moves:
            if m.get("type") == "play_cards" and m.get("cards"):
                return {"type": "play_cards", "cards": m.get("cards")}
        return {"type": "pass", "cards": []}
    
    def is_available(self) -> bool:
        """Check if any models are available"""
        return self.models_loaded
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        info = {
            "enhanced_provider": True,
            "general_model_available": os.path.exists(self.general_model_path),
            "general_model_path": self.general_model_path,
        }
        
        if self.bao_sam_provider:
            bao_sam_info = self.bao_sam_provider.get_model_info()
            info.update({
                "bao_sam_models_available": bao_sam_info.get("models_loaded", False),
                "bao_sam_decision_model": bao_sam_info.get("decision_model_loaded", False),
                "bao_sam_combo_model": bao_sam_info.get("combo_model_loaded", False),
            })
        
        return info
