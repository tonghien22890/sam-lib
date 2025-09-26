"""
Sam Strategy

Sam-specific AI strategy implementing Sam game logic
and decision-making patterns.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import time
import logging

from .base_strategy import BaseStrategy, StrategyConfig

logger = logging.getLogger(__name__)


class SamStrategy(BaseStrategy):
    """
    Sam-specific AI strategy.
    
    Implements Sam game logic including:
    - Báo Sâm declaration logic
    - Tới trắng detection
    - Chặt rules
    - Penalty avoidance
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        Initialize Sam strategy
        
        Args:
            config: Strategy configuration (optional)
        """
        if config is None:
            config = StrategyConfig(
                name="sam_strategy",
                game_type="sam",
                aggressiveness=0.5,  # Balanced for Sam
                risk_tolerance=0.4   # Lower risk tolerance for Sam
            )
        
        super().__init__(config)
        self._sam_features = {}
    
    def evaluate_move(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """
        Evaluate a move for Sam with game-specific considerations.
        
        Args:
            move: Move to evaluate
            game_state: Current game state
            
        Returns:
            float: Move score (higher is better)
        """
        base_score = self._evaluate_base_move(move, game_state)
        
        # Apply Sam-specific enhancements
        sam_score = self._apply_sam_scoring(move, game_state, base_score)
        
        return sam_score
    
    def select_best_move(self, legal_moves: List[Dict[str, Any]], 
                        game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the best move for Sam.
        
        Args:
            legal_moves: Available legal moves
            game_state: Current game state
            
        Returns:
            Dict containing the selected move
        """
        if not legal_moves:
            return {'type': 'pass', 'cards': []}
        
        # Evaluate all legal moves
        scored_moves = []
        for move in legal_moves:
            score = self.evaluate_move(move, game_state)
            scored_moves.append((move, score))
        
        # Select move with highest score
        best_move, best_score = max(scored_moves, key=lambda x: x[1])
        
        self.logger.debug(f"Sam Strategy: Selected move {best_move} with score {best_score:.3f}")
        
        return best_move
    
    def should_declare_special(self, game_state: Dict[str, Any]) -> bool:
        """
        Determine if should declare Báo Sâm.
        
        Args:
            game_state: Current game state
            
        Returns:
            bool: True if should declare Báo Sâm
        """
        # Check if in Báo Sâm phase
        if not game_state.get('bao_sam_phase', False):
            return False
        
        # Check if should declare based on hand strength
        hand = game_state.get('hand', [])
        if not hand:
            return False
        
        # Simple Báo Sâm logic: declare if hand is strong enough
        hand_strength = self._calculate_hand_strength(hand)
        threshold = 0.7  # Threshold for Báo Sâm declaration
        
        return hand_strength >= threshold
    
    def _evaluate_base_move(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """
        Evaluate base move without Sam-specific logic.
        
        Args:
            move: Move to evaluate
            game_state: Current game state
            
        Returns:
            float: Base move score
        """
        if move.get('type') == 'pass':
            return 0.1  # Low score for passing
        
        if move.get('type') == 'play_cards':
            cards = move.get('cards', [])
            if not cards:
                return 0.0
            
            # Base scoring on combo strength
            combo_type = move.get('combo_type', 'unknown')
            rank_value = move.get('rank_value', 0)
            
            # Higher rank = higher score
            base_score = rank_value / 12.0
            
            # Bonus for certain combo types
            if combo_type in ['straight', 'double_seq']:
                base_score += 0.2
            
            return base_score
        
        return 0.0
    
    def _apply_sam_scoring(self, move: Dict[str, Any], game_state: Dict[str, Any], 
                          base_score: float) -> float:
        """
        Apply Sam-specific scoring enhancements.
        
        Args:
            move: Move to evaluate
            game_state: Current game state
            base_score: Base move score
            
        Returns:
            float: Enhanced score
        """
        enhanced_score = base_score
        
        # Consider Báo Sâm implications
        bao_sam_bonus = self._calculate_bao_sam_bonus(move, game_state)
        enhanced_score += bao_sam_bonus
        
        # Consider chặt opportunities
        chat_bonus = self._calculate_chat_bonus(move, game_state)
        enhanced_score += chat_bonus
        
        # Consider penalty avoidance
        penalty_penalty = self._calculate_penalty_penalty(move, game_state)
        enhanced_score -= penalty_penalty
        
        return max(0.0, enhanced_score)  # Ensure non-negative score
    
    def _calculate_hand_strength(self, hand: List[int]) -> float:
        """
        Calculate hand strength for Báo Sâm decision.
        
        Args:
            hand: Current hand
            
        Returns:
            float: Hand strength (0.0 to 1.0)
        """
        if not hand:
            return 0.0
        
        # Simple hand strength calculation
        # Higher cards = stronger hand
        total_value = sum(card % 13 for card in hand)
        max_possible = len(hand) * 12  # All cards are 2s (rank 12)
        
        return total_value / max_possible if max_possible > 0 else 0.0
    
    def _calculate_bao_sam_bonus(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate Báo Sâm bonus."""
        # Placeholder - implement Báo Sâm logic
        return 0.0
    
    def _calculate_chat_bonus(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate chặt opportunity bonus."""
        # Placeholder - implement chặt logic
        return 0.0
    
    def _calculate_penalty_penalty(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate penalty avoidance penalty."""
        # Placeholder - implement penalty logic
        return 0.0
