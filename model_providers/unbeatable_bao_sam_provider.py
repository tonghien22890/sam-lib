"""
Unbeatable Báo Sâm Model Provider
Integrates the new Unbeatable Sequence Model into the game system
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ai_common.bots.model_bot import ModelProvider
from ai_common.adapters.unbeatable_adapter import UnbeatableAdapter

logger = logging.getLogger(__name__)

class UnbeatableBaoSamProvider(ModelProvider):
    """Production-ready Báo Sâm provider using Unbeatable Sequence Model"""
    
    def __init__(self, model_dir: Optional[str] = None) -> None:
        super().__init__(name="unbeatable_bao_sam", version="v1")
        self.adapter = UnbeatableAdapter(model_dir)
        self.decision_count = 0
        self.correct_decisions = 0
        self.accuracy_log = []
        
        logger.info("UnbeatableBaoSamProvider initialized")
    
    def _ensure_loaded(self) -> bool:
        """Ensure the model is loaded and ready"""
        return self.adapter.ensure_ready()
    
    def predict(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict action for ModelBot compatibility"""
        # For Báo Sâm decisions, we need to analyze the current hand
        hand = game_record.get('hand', [])
        player_count = game_record.get('player_count', 4)
        
        # If this is a Báo Sâm declaration decision, use our specialized logic
        if game_record.get('game_type') == 'sam' and any(move.get('type') == 'declare_bao_sam' for move in legal_moves):
            return self._analyze_bao_sam_declaration(hand, player_count, legal_moves)
        
        # For regular moves, use standard logic
        for move in legal_moves:
            if move.get("type") == "play_cards" and move.get("cards"):
                return {"type": "play_cards", "cards": move.get("cards")}
        
        return {"type": "pass", "cards": []}
    
    def _analyze_bao_sam_declaration(self, hand: List[int], player_count: int, legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze whether to declare Báo Sâm using Unbeatable Sequence Model"""
        if not self._ensure_loaded():
            # Fallback: conservative decision
            logger.warning("UnbeatableBaoSamProvider: Model not loaded, using fallback")
            return {"type": "pass", "cards": []}
        
        # Use the Unbeatable Sequence Model
        decision_result = self.adapter.should_declare_bao_sam(hand, player_count)
        
        # Log decision for accuracy tracking
        self.decision_count += 1
        self.accuracy_log.append({
            'timestamp': datetime.now().isoformat(),
            'hand': hand,
            'player_count': player_count,
            'decision': decision_result,
            'should_declare': decision_result['should_declare']
        })
        
        # If model says we should declare, find the declare_bao_sam move
        if decision_result['should_declare']:
            for move in legal_moves:
                if move.get('type') == 'declare_bao_sam':
                    logger.info(f"UnbeatableBaoSamProvider: Declaring Báo Sâm - "
                              f"Prob: {decision_result['unbeatable_probability']:.3f}, "
                              f"Threshold: {decision_result['user_threshold']:.3f}")
                    return move
        
        # Otherwise, play cards normally
        for move in legal_moves:
            if move.get("type") == "play_cards" and move.get("cards"):
                return {"type": "play_cards", "cards": move.get("cards")}
        
        return {"type": "pass", "cards": []}
    
    def predict_bao_sam_decision(self, hand: List[int], second_arg: Optional[Any] = None) -> Dict[str, Any]:
        """Make Báo Sâm decision for given hand using Unbeatable Sequence Model

        Backward-compatible signature:
        - Old: (hand, combo_sequence: List[Dict]) → we ignore sequence, assume 4 players
        - New: (hand, player_count: int)
        """
        # Determine player_count from second_arg while keeping backward compatibility
        player_count: int = 4
        if isinstance(second_arg, int):
            player_count = second_arg
        else:
            # If it's a list/dict/None (old signature), keep default 4
            player_count = 4

        if not self._ensure_loaded():
            return {
                'should_declare': False,
                'confidence': 0.0,
                'reason': 'model_not_loaded',
                'timestamp': datetime.now().isoformat()
            }
        
        # Use the adapter
        result = self.adapter.should_declare_bao_sam(hand, player_count)
        
        # Log decision
        self.decision_count += 1
        self.accuracy_log.append({
            'timestamp': datetime.now().isoformat(),
            'hand': hand,
            'player_count': player_count,
            'decision': result,
            'should_declare': result['should_declare']
        })
        
        # Convert to expected format
        return {
            'should_declare': result['should_declare'],
            'confidence': result['model_confidence'],
            'unbeatable_probability': result['unbeatable_probability'],
            'user_threshold': result['user_threshold'],
            'reason': result['reason'],
            'unbeatable_sequence': result.get('unbeatable_sequence'),
            'sequence_stats': result.get('sequence_stats'),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of the loaded model"""
        return self.adapter.get_model_status()

    def get_model_info(self) -> Dict[str, Any]:
        """Backward-compatible info method used by web_backend/app.py

        Maps the Unbeatable model status to the legacy info schema.
        """
        status = self.get_model_status()
        return {
            "models_available": bool(status.get('loaded', False)),
            "models_loaded": bool(status.get('loaded', False)),
            "decision_model_loaded": 'validation_model.pkl' in status.get('trained_models', []),
            "combo_model_loaded": True,  # sequence generation is rule+ML inside generator
            "models_dir": status.get('model_dir')
        }
    
    def get_accuracy_stats(self) -> Dict[str, Any]:
        """Get accuracy statistics"""
        if self.decision_count == 0:
            return {
                'accuracy': 0.0, 
                'total_decisions': 0, 
                'correct_decisions': 0,
                'recent_decisions': []
            }
        
        accuracy = self.correct_decisions / self.decision_count
        
        # Get recent decisions (last 10)
        recent_decisions = self.accuracy_log[-10:] if len(self.accuracy_log) > 10 else self.accuracy_log
        
        return {
            'overall_accuracy': accuracy,
            'total_decisions': self.decision_count,
            'correct_decisions': self.correct_decisions,
            'recent_decisions': recent_decisions
        }
    
    def record_correct_decision(self, was_correct: bool):
        """Record whether the last decision was correct"""
        if was_correct:
            self.correct_decisions += 1

# Global instance
_unbeatable_provider = None

def get_unbeatable_bao_sam_provider(model_dir: Optional[str] = None) -> UnbeatableBaoSamProvider:
    """Get singleton instance of Unbeatable Báo Sâm provider"""
    global _unbeatable_provider
    if _unbeatable_provider is None:
        _unbeatable_provider = UnbeatableBaoSamProvider(model_dir)
        logger.info("Initialized Unbeatable Báo Sâm Provider")
    return _unbeatable_provider
