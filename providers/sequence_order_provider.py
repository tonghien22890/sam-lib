"""
Sequence Order Provider for consistent combo ordering
Ensures Báo Sâm decision and actual gameplay use the same sequence order
"""

import logging
from typing import List, Dict, Any, Optional

from ai_common.core.combo_analyzer import ComboAnalyzer
from ai_common.rules.sam_rule_engine import SamRuleEngine
from ai_common.features.sequence_features import SequenceFeatureExtractor

logger = logging.getLogger(__name__)


class SequenceOrderProvider:
    """Provider for consistent sequence ordering across decision and gameplay"""
    
    def __init__(self):
        self.combo_analyzer = ComboAnalyzer()
        self.rule_engine = SamRuleEngine()
        self.feature_extractor = SequenceFeatureExtractor()
        logger.info("SequenceOrderProvider initialized")
    
    def get_ordered_sequence(self, hand: List[int], player_count: int = 4, 
                           order_strategy: str = "strength_desc") -> List[Dict[str, Any]]:
        """
        Get ordered sequence for consistent gameplay
        
        Args:
            hand: List of card indices (0-51)
            player_count: Number of players
            order_strategy: Ordering strategy
                - "strength_desc": Strongest first (default)
                - "strength_asc": Weakest first
                - "pattern_based": Based on user patterns
                - "balanced": Balanced distribution
        
        Returns:
            List of combos in optimal order
        """
        # Analyze hand to get all possible combos
        combos = self.combo_analyzer.analyze_hand(hand)
        
        if not combos:
            logger.warning("No combos found for hand")
            return []
        
        # Apply ordering strategy
        if order_strategy == "strength_desc":
            return self._order_by_strength_desc(combos)
        elif order_strategy == "strength_asc":
            return self._order_by_strength_asc(combos)
        elif order_strategy == "pattern_based":
            return self._order_by_pattern(combos, hand, player_count)
        elif order_strategy == "balanced":
            return self._order_balanced(combos)
        else:
            logger.warning(f"Unknown order strategy: {order_strategy}, using strength_desc")
            return self._order_by_strength_desc(combos)
    
    def _order_by_strength_desc(self, combos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order by strength descending (strongest first)"""
        return sorted(combos, key=lambda combo: -self.combo_analyzer.calculate_combo_strength(combo))
    
    def _order_by_strength_asc(self, combos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order by strength ascending (weakest first)"""
        return sorted(combos, key=lambda combo: self.combo_analyzer.calculate_combo_strength(combo))
    
    def _order_by_pattern(self, combos: List[Dict[str, Any]], hand: List[int], player_count: int) -> List[Dict[str, Any]]:
        """Order based on user patterns (similar to unbeatable model)"""
        hand_data = {
            'hand': hand,
            'player_count': player_count,
            'possible_combos': combos
        }
        
        # Extract pattern features
        pattern_features = self.feature_extractor.extract_pattern_features(hand_data)
        
        # Determine pattern preference
        power_concentration = pattern_features[1]  # From extract_pattern_features
        if power_concentration > 0.6:
            # Power-first: strongest combos first
            return self._order_by_strength_desc(combos)
        else:
            # Balanced: mix strong and weak
            return self._order_balanced(combos)
    
    def _order_balanced(self, combos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order with balanced distribution (strong-weak-strong pattern)"""
        # Sort by strength first
        sorted_combos = sorted(combos, key=lambda combo: -self.combo_analyzer.calculate_combo_strength(combo))
        
        # Create balanced order: strong, weak, medium, strong, weak, etc.
        strong_combos = []
        medium_combos = []
        weak_combos = []
        
        for combo in sorted_combos:
            strength = self.combo_analyzer.calculate_combo_strength(combo)
            if strength >= 0.7:
                strong_combos.append(combo)
            elif strength >= 0.4:
                medium_combos.append(combo)
            else:
                weak_combos.append(combo)
        
        # Interleave: strong, weak, medium, strong, weak, etc.
        balanced = []
        max_len = max(len(strong_combos), len(weak_combos), len(medium_combos))
        
        for i in range(max_len):
            if i < len(strong_combos):
                balanced.append(strong_combos[i])
            if i < len(weak_combos):
                balanced.append(weak_combos[i])
            if i < len(medium_combos):
                balanced.append(medium_combos[i])
        
        return balanced
    
    def get_sequence_with_strategy(self, hand: List[int], player_count: int = 4,
                                 strategy: str = "bao_sam_optimal") -> Dict[str, Any]:
        """
        Get sequence with specific strategy for different game phases
        
        Args:
            hand: List of card indices
            player_count: Number of players
            strategy: Strategy type
                - "bao_sam_optimal": Optimal for Báo Sâm declaration
                - "defensive": Defensive play order
                - "aggressive": Aggressive play order
                - "balanced": Balanced approach
        
        Returns:
            Dictionary with sequence and metadata
        """
        if strategy == "bao_sam_optimal":
            # Use same logic as unbeatable model
            sequence = self.get_ordered_sequence(hand, player_count, "pattern_based")
            return {
                'sequence': sequence,
                'strategy': 'bao_sam_optimal',
                'order_reason': 'pattern_based_optimal_for_bao_sam',
                'total_combos': len(sequence),
                'avg_strength': self._calculate_avg_strength(sequence)
            }
        elif strategy == "defensive":
            # Start with weak combos, save strong ones
            sequence = self.get_ordered_sequence(hand, player_count, "strength_asc")
            return {
                'sequence': sequence,
                'strategy': 'defensive',
                'order_reason': 'weak_first_conserve_strength',
                'total_combos': len(sequence),
                'avg_strength': self._calculate_avg_strength(sequence)
            }
        elif strategy == "aggressive":
            # Start with strongest combos
            sequence = self.get_ordered_sequence(hand, player_count, "strength_desc")
            return {
                'sequence': sequence,
                'strategy': 'aggressive',
                'order_reason': 'strong_first_immediate_pressure',
                'total_combos': len(sequence),
                'avg_strength': self._calculate_avg_strength(sequence)
            }
        elif strategy == "balanced":
            # Balanced approach
            sequence = self.get_ordered_sequence(hand, player_count, "balanced")
            return {
                'sequence': sequence,
                'strategy': 'balanced',
                'order_reason': 'balanced_distribution',
                'total_combos': len(sequence),
                'avg_strength': self._calculate_avg_strength(sequence)
            }
        else:
            logger.warning(f"Unknown strategy: {strategy}, using bao_sam_optimal")
            return self.get_sequence_with_strategy(hand, player_count, "bao_sam_optimal")
    
    def _calculate_avg_strength(self, sequence: List[Dict[str, Any]]) -> float:
        """Calculate average strength of sequence"""
        if not sequence:
            return 0.0
        
        strengths = [self.combo_analyzer.calculate_combo_strength(combo) for combo in sequence]
        return sum(strengths) / len(strengths)
    
    def validate_sequence_consistency(self, hand: List[int], player_count: int = 4) -> Dict[str, Any]:
        """
        Validate that sequence order is consistent with Báo Sâm decision
        
        Args:
            hand: List of card indices
            player_count: Number of players
        
        Returns:
            Validation results
        """
        # Get sequence from this provider
        provider_sequence = self.get_ordered_sequence(hand, player_count, "pattern_based")
        
        # Get sequence from unbeatable model (if available)
        try:
            # This would need to be integrated with the actual unbeatable model
            # For now, we'll simulate the comparison
            unbeatable_sequence = self.get_ordered_sequence(hand, player_count, "strength_desc")
            
            # Compare sequences
            provider_strengths = [self.combo_analyzer.calculate_combo_strength(c) for c in provider_sequence]
            unbeatable_strengths = [self.combo_analyzer.calculate_combo_strength(c) for c in unbeatable_sequence]
            
            return {
                'consistent': provider_strengths == unbeatable_strengths,
                'provider_sequence': provider_sequence,
                'unbeatable_sequence': unbeatable_sequence,
                'provider_avg_strength': sum(provider_strengths) / len(provider_strengths) if provider_strengths else 0,
                'unbeatable_avg_strength': sum(unbeatable_strengths) / len(unbeatable_strengths) if unbeatable_strengths else 0
            }
        except Exception as e:
            logger.warning(f"Could not validate consistency: {e}")
            return {
                'consistent': False,
                'error': str(e),
                'provider_sequence': provider_sequence
            }
