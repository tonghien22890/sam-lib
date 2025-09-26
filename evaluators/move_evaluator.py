"""
Advanced Move Evaluator - Sophisticated move evaluation logic
"""

from typing import List, Dict, Set, Optional
from game_engine.core.card_encoding import Card, Rank, Suit
from game_engine.core.game_entities import Move, GameState
from game_engine.core.combo_validator import ComboType
from ..penalty_avoidance.penalty_checker import PenaltyChecker
from ..penalty_avoidance.penalty_types import PenaltyRisk


class MoveEvaluator:
    """Advanced move evaluation with multiple criteria"""
    
    def __init__(self):
        self.penalty_checker = PenaltyChecker()
    
    def evaluate_move(
        self, 
        move: Move, 
        hand: List[Card], 
        game_state: GameState,
        game_type: str = "tlmn"
    ) -> float:
        """
        Evaluate a move with comprehensive scoring
        
        Returns:
            Score from 0.0 (worst) to 1.0 (best)
        """
        if not hasattr(move, 'cards') or not move.cards:
            return 0.0
        
        score = 0.0
        
        # 1. Penalty avoidance (40% weight)
        penalty_score = self._evaluate_penalty_avoidance(move, hand, game_state, game_type)
        score += penalty_score * 0.4
        
        # 2. Card value optimization (25% weight)
        card_value_score = self._evaluate_card_values(move, hand)
        score += card_value_score * 0.25
        
        # 3. Combo efficiency (20% weight)
        combo_score = self._evaluate_combo_efficiency(move)
        score += combo_score * 0.2
        
        # 4. Strategic value (15% weight)
        strategic_score = self._evaluate_strategic_value(move, hand, game_state)
        score += strategic_score * 0.15
        
        # Ensure minimum score for any valid move
        return max(0.1, min(1.0, score))
    
    def _evaluate_penalty_avoidance(
        self, 
        move: Move, 
        hand: List[Card], 
        game_state: GameState,
        game_type: str
    ) -> float:
        """Evaluate how well the move avoids penalties"""
        score = 1.0
        
        # Simulate hand after move
        remaining_hand = [card for card in hand if card not in move.cards]
        
        # Check penalty risks in remaining hand
        if game_type == "tlmn":
            risks = self.penalty_checker.check_tlmn_penalties(remaining_hand, game_state)
        else:
            risks = self.penalty_checker.check_sam_penalties(remaining_hand, game_state)
        
        # Heavy penalty for critical risks
        for risk in risks:
            severity = self.penalty_checker.get_penalty_severity(risk)
            if severity.value >= 3:  # CRITICAL
                score -= 0.8
            elif severity.value >= 2:  # HIGH
                score -= 0.4
            elif severity.value >= 1:  # MEDIUM
                score -= 0.2
        
        # Bonus for getting rid of dangerous cards
        for card in move.cards:
            if card.rank == Rank.TWO and card.suit == Suit.SPADES:  # 2♠
                score += 0.3
            elif card.rank == Rank.TWO:  # Other 2s
                score += 0.2
            elif card.rank.value >= 10:  # High cards
                score += 0.1
        
        return max(0.0, score)
    
    def _evaluate_card_values(self, move: Move, hand: List[Card]) -> float:
        """Evaluate card value optimization"""
        if not move.cards:
            return 0.0
        
        # Prefer getting rid of high-value cards
        total_value = sum(card.rank.value for card in move.cards)
        avg_value = total_value / len(move.cards)
        
        # Invert so lower values score higher (we want to get rid of high cards)
        score = (12 - avg_value) / 12.0
        
        # Bonus for getting rid of multiple high cards
        high_cards = sum(1 for card in move.cards if card.rank.value >= 8)
        if high_cards > 1:
            score += 0.2
        
        return min(1.0, score)
    
    def _evaluate_combo_efficiency(self, move: Move) -> float:
        """Evaluate combo efficiency"""
        if not hasattr(move, 'combo_type'):
            return 0.5
        
        # Combo type preferences
        combo_preferences = {
            ComboType.SINGLE: 0.3,      # Basic, good for dumping
            ComboType.PAIR: 0.5,        # Good for clearing pairs
            ComboType.TRIPLE: 0.7,      # Very good for clearing
            ComboType.FOUR_KIND: 0.9,   # Excellent, powerful
            ComboType.STRAIGHT: 0.6,    # Good for clearing multiple
            ComboType.DOUBLE_SEQ: 0.8,  # Very good for clearing
            ComboType.THREE_CONSECUTIVE_PAIRS: 0.9,  # Powerful
            ComboType.FOUR_CONSECUTIVE_PAIRS: 1.0,   # Most powerful
            ComboType.SPECIAL: 1.0      # Best, rare combos
        }
        
        return combo_preferences.get(move.combo_type, 0.5)
    
    def _evaluate_strategic_value(
        self, 
        move: Move, 
        hand: List[Card], 
        game_state: GameState
    ) -> float:
        """Evaluate strategic value of the move"""
        score = 0.5  # Base score
        
        # Hand size consideration
        hand_size = len(hand)
        if hand_size <= 3:
            # Urgent to play when few cards left
            score += 0.3
        elif hand_size <= 6:
            score += 0.1
        
        # Opponent hand sizes
        opponent_hands = [len(p.hand) for p in game_state.players]
        if opponent_hands:
            min_opponent_hand = min(opponent_hands)
            if min_opponent_hand <= 2:
                # Someone is close to winning, play more aggressively
                score += 0.2
        
        # Game phase consideration
        total_cards_played = sum(13 - len(p.hand) for p in game_state.players)
        if total_cards_played > 30:  # Late game
            score += 0.1
        
        return min(1.0, score)
    
    def get_move_rankings(
        self, 
        moves: List[Move], 
        hand: List[Card], 
        game_state: GameState,
        game_type: str = "tlmn"
    ) -> List[tuple[Move, float]]:
        """Get moves ranked by evaluation score"""
        scored_moves = []
        
        for move in moves:
            score = self.evaluate_move(move, hand, game_state, game_type)
            scored_moves.append((move, score))
        
        # Sort by score (highest first)
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        return scored_moves
