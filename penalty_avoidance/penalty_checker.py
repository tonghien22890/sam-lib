"""
Penalty Checker - Common penalty avoidance logic for all AI
"""

from typing import List, Dict, Set
from game_engine.core.card_encoding import Card, Rank, Suit
from game_engine.core.game_entities import GameState
from game_engine.core.combo_validator import ComboValidator, ComboType
from .penalty_types import PenaltyRisk, PenaltySeverity


class PenaltyChecker:
    """Common penalty avoidance logic for all AI"""
    
    def __init__(self):
        self.combo_validator = ComboValidator()
    
    def check_tlmn_penalties(self, hand: List[Card], game_state: GameState) -> List[PenaltyRisk]:
        """Check TLMN penalty risks"""
        risks = []
        
        # Check for 2♠ (highest penalty risk)
        if self._has_2_spades(hand):
            risks.append(PenaltyRisk.THOI_2_SPADES)
        
        # Check for four of a kind
        if self._has_four_of_kind(hand):
            risks.append(PenaltyRisk.THOI_FOUR_KIND)
        
        # Check for 3 đôi thông
        if self._has_three_consecutive_pairs(hand):
            risks.append(PenaltyRisk.THOI_THREE_PAIRS)
        
        # Check for 4 đôi thông
        if self._has_four_consecutive_pairs(hand):
            risks.append(PenaltyRisk.THOI_FOUR_PAIRS)
        
        return risks
    
    def check_sam_penalties(self, hand: List[Card], game_state: GameState) -> List[PenaltyRisk]:
        """Check Sam penalty risks"""
        risks = []
        
        # Check for 2♠
        if self._has_2_spades(hand):
            risks.append(PenaltyRisk.THOI_2_SPADES_SAM)
        
        # Check for four of a kind
        if self._has_four_of_kind(hand):
            risks.append(PenaltyRisk.THOI_FOUR_KIND_SAM)
        
        # Check for Cóng risk
        if self._risk_of_cong(hand, game_state):
            risks.append(PenaltyRisk.CONG)
        
        return risks
    
    def _has_2_spades(self, hand: List[Card]) -> bool:
        """Check if hand contains 2♠"""
        return any(card.rank == Rank.TWO and card.suit == Suit.SPADES for card in hand)
    
    def _has_four_of_kind(self, hand: List[Card]) -> bool:
        """Check if hand contains four of a kind"""
        rank_counts = {}
        for card in hand:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        
        return any(count >= 4 for count in rank_counts.values())
    
    def _has_three_consecutive_pairs(self, hand: List[Card]) -> bool:
        """Check if hand contains 3 đôi thông"""
        rank_counts = {}
        for card in hand:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        
        # Find pairs (at least 2 cards of same rank)
        pairs = [rank for rank, count in rank_counts.items() if count >= 2]
        pairs.sort(key=lambda r: r.value)
        
        # Check for 3 consecutive pairs
        for i in range(len(pairs) - 2):
            if (pairs[i+1].value == pairs[i].value + 1 and 
                pairs[i+2].value == pairs[i].value + 2):
                return True
        
        return False
    
    def _has_four_consecutive_pairs(self, hand: List[Card]) -> bool:
        """Check if hand contains 4 đôi thông"""
        rank_counts = {}
        for card in hand:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        
        # Find pairs
        pairs = [rank for rank, count in rank_counts.items() if count >= 2]
        pairs.sort(key=lambda r: r.value)
        
        # Check for 4 consecutive pairs
        for i in range(len(pairs) - 3):
            if (pairs[i+1].value == pairs[i].value + 1 and 
                pairs[i+2].value == pairs[i].value + 2 and
                pairs[i+3].value == pairs[i].value + 3):
                return True
        
        return False
    
    def _risk_of_cong(self, hand: List[Card], game_state: GameState) -> bool:
        """Check if there's risk of Cóng (can't play any card)"""
        # Simplified check - in reality this would be more complex
        # Cóng happens when you can't play any legal move
        return len(hand) > 5  # High risk if many cards left
    
    def get_penalty_severity(self, risk: PenaltyRisk) -> PenaltySeverity:
        """Get the severity of a penalty risk"""
        critical_penalties = {
            PenaltyRisk.THOI_2_SPADES,
            PenaltyRisk.THOI_FOUR_KIND,
            PenaltyRisk.THOI_THREE_PAIRS,
            PenaltyRisk.THOI_FOUR_PAIRS,
            PenaltyRisk.THOI_2_SPADES_SAM,
            PenaltyRisk.THOI_FOUR_KIND_SAM,
            PenaltyRisk.CONG,
            PenaltyRisk.PHAT_SAM
        }
        
        if risk in critical_penalties:
            return PenaltySeverity.CRITICAL
        else:
            return PenaltySeverity.LOW
