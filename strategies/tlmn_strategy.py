"""
TLMN Strategy

TLMN-specific AI strategy implementing TLMN game logic
and decision-making patterns.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import time
import logging

from .base_strategy import BaseStrategy, StrategyConfig

logger = logging.getLogger(__name__)


class TLMNStrategy(BaseStrategy):
    """
    TLMN-specific AI strategy.
    
    Implements TLMN game logic including:
    - Color-based scoring awareness
    - End-game rule enforcement
    - Chặt logic integration
    - Kết 3 bích consideration
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        Initialize TLMN strategy
        
        Args:
            config: Strategy configuration (optional)
        """
        if config is None:
            config = StrategyConfig(
                name="tlmn_strategy",
                game_type="tlmn",
                aggressiveness=0.6,  # Slightly aggressive for TLMN
                risk_tolerance=0.7   # Higher risk tolerance for TLMN
            )
        
        super().__init__(config)
        self._tlmn_features = {}
    
    def evaluate_move(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """
        Evaluate a move for TLMN with game-specific considerations.
        
        Args:
            move: Move to evaluate
            game_state: Current game state
            
        Returns:
            float: Move score (higher is better)
        """
        base_score = self._evaluate_base_move(move, game_state)
        
        # Apply TLMN-specific enhancements
        tlmn_score = self._apply_tlmn_scoring(move, game_state, base_score)
        
        return tlmn_score
    
    def select_best_move(self, legal_moves: List[Dict[str, Any]], 
                        game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the best move for TLMN.
        
        Args:
            legal_moves: Available legal moves
            game_state: Current game state
            
        Returns:
            Dict containing the selected move
        """
        if not legal_moves:
            return {'type': 'pass', 'cards': []}
        
        # Filter moves according to TLMN rules
        valid_moves = self._filter_tlmn_moves(legal_moves, game_state)
        
        if not valid_moves:
            return {'type': 'pass', 'cards': []}
        
        # Evaluate all valid moves
        scored_moves = []
        for move in valid_moves:
            score = self.evaluate_move(move, game_state)
            scored_moves.append((move, score))
        
        # Select move with highest score
        best_move, best_score = max(scored_moves, key=lambda x: x[1])
        
        self.logger.debug(f"TLMN Strategy: Selected move {best_move} with score {best_score:.3f}")
        
        return best_move
    
    def should_declare_special(self, game_state: Dict[str, Any]) -> bool:
        """
        Determine if should declare special TLMN actions.
        
        Args:
            game_state: Current game state
            
        Returns:
            bool: True if should declare special action
        """
        # TLMN doesn't have Báo Sâm, but could have other special declarations
        # For now, return False
        return False
    
    def _evaluate_base_move(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """
        Evaluate base move without TLMN-specific logic.
        
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
    
    def _apply_tlmn_scoring(self, move: Dict[str, Any], game_state: Dict[str, Any], 
                           base_score: float) -> float:
        """
        Apply TLMN-specific scoring enhancements.
        
        Args:
            move: Move to evaluate
            game_state: Current game state
            base_score: Base move score
            
        Returns:
            float: Enhanced score
        """
        enhanced_score = base_score
        
        # Consider color-based scoring
        color_bonus = self._calculate_color_bonus(move, game_state)
        enhanced_score += color_bonus
        
        # Consider chặt opportunities
        chat_bonus = self._calculate_chat_bonus(move, game_state)
        enhanced_score += chat_bonus
        
        # Consider end-game rules
        end_game_penalty = self._calculate_end_game_penalty(move, game_state)
        enhanced_score -= end_game_penalty
        
        # Consider Kết 3 bích
        ket_3_bich_bonus = self._calculate_ket_3_bich_bonus(move, game_state)
        enhanced_score += ket_3_bich_bonus
        
        return max(0.0, enhanced_score)  # Ensure non-negative score
    
    def _filter_tlmn_moves(self, legal_moves: List[Dict[str, Any]], 
                          game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter moves according to TLMN rules.
        
        Args:
            legal_moves: Available moves
            game_state: Current game state
            
        Returns:
            List of valid TLMN moves
        """
        valid_moves = []
        
        for move in legal_moves:
            if self._is_valid_tlmn_move(move, game_state):
                valid_moves.append(move)
        
        return valid_moves
    
    def _is_valid_tlmn_move(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> bool:
        """
        Check if move is valid according to TLMN rules.
        
        Args:
            move: Move to check
            game_state: Current game state
            
        Returns:
            bool: True if valid
        """
        if move.get('type') != 'play_cards':
            return True
        
        # Check TLMN end rules
        if self._violates_tlmn_end_rules(move, game_state):
            return False
        
        return True
    
    def _violates_tlmn_end_rules(self, move: Dict[str, Any], 
                                game_state: Dict[str, Any]) -> bool:
        """
        Check if move violates TLMN end rules.
        
        Args:
            move: Move to check
            game_state: Current game state
            
        Returns:
            bool: True if violates rules
        """
        cards = move.get('cards', [])
        if not cards:
            return False
        
        # Check if this would be the last move
        hand = game_state.get('hand', [])
        remaining_cards = [card for card in hand if card not in cards]
        
        if not remaining_cards:  # This is the last move
            # Check if ending with 2 or four-of-a-kind
            if self._ends_with_2_or_four_kind(cards):
                return True
        
        # Check if would leave only 2s
        if remaining_cards and all(self._is_2_card(card) for card in remaining_cards):
            return True
        
        # Check if would leave exactly a four-of-a-kind
        if len(remaining_cards) == 4:
            if self._is_four_of_a_kind(remaining_cards):
                return True
        
        return False
    
    def _ends_with_2_or_four_kind(self, cards: List[int]) -> bool:
        """Check if cards end with 2 or four-of-a-kind."""
        if not cards:
            return False
        
        # Check if contains 2
        if any(self._is_2_card(card) for card in cards):
            return True
        
        # Check if is four-of-a-kind
        if len(cards) == 4 and self._is_four_of_a_kind(cards):
            return True
        
        return False
    
    def _is_2_card(self, card: int) -> bool:
        """Check if card is a 2."""
        return card in [12, 25, 38, 51]
    
    def _is_four_of_a_kind(self, cards: List[int]) -> bool:
        """Check if cards form a four-of-a-kind."""
        if len(cards) != 4:
            return False
        
        ranks = [card % 13 for card in cards]
        return len(set(ranks)) == 1
    
    def _calculate_color_bonus(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate color-based scoring bonus."""
        # Placeholder - implement color scoring logic
        return 0.0
    
    def _calculate_chat_bonus(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate chặt opportunity bonus."""
        # Placeholder - implement chặt logic
        return 0.0
    
    def _calculate_end_game_penalty(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate end-game rule penalty."""
        if self._violates_tlmn_end_rules(move, game_state):
            return 1.0  # High penalty for violating end rules
        return 0.0
    
    def _calculate_ket_3_bich_bonus(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """Calculate Kết 3 bích bonus."""
        cards = move.get('cards', [])
        if not cards:
            return 0.0
        
        # Check if this move would end with 3♠
        if len(cards) == 1 and cards[0] == 12:  # 3♠ is card 12
            return 0.5  # Bonus for Kết 3 bích
        
        return 0.0
