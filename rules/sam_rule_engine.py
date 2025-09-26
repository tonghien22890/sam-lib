"""
Sam game rule validation engine
Extracted from model_build/scripts/unbeatable/unbeatable_sequence_model.py
"""

import numpy as np
import logging
from typing import List, Dict, Any, Tuple

from ai_common.core.combo_analyzer import ComboAnalyzer

logger = logging.getLogger(__name__)


class SamRuleEngine:
    """Rulebase validation layer for Sam game - chặn bài quá yếu"""
    
    def __init__(self):
        self.rules = {
            'min_total_cards': 10,           # Đủ bài để tạo sequence
            'max_weak_combos': 1,            # Tối đa 1 combo < 0.5 strength
            'min_strong_combos': 1,          # Ít nhất 1 combo >= 0.7 strength
            'min_avg_strength': 0.55,        # Trung bình strength >= 0.55 (allow borderline)
            'min_unbeatable_combos': 1,      # Ít nhất 1 combo strength >= 0.8
        }
        logger.info(f"SamRuleEngine initialized with rules: {self.rules}")
    
    def validate_hand(self, possible_combos: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate hand against Sam game rules
        
        Args:
            possible_combos: List of combo dictionaries from hand analysis
            
        Returns:
            Tuple of (is_valid, reason, strength_profile)
        """
        if not possible_combos:
            return False, "no_combos_found", {}
        
        # Calculate total cards
        total_cards = sum(len(combo.get('cards', [])) for combo in possible_combos)
        
        # Calculate strengths
        strengths = [ComboAnalyzer.calculate_combo_strength(combo) for combo in possible_combos]
        
        # Rule checks
        if total_cards < self.rules['min_total_cards']:
            return False, f"insufficient_cards_{total_cards}", {}
        
        weak_combos = sum(1 for s in strengths if s < 0.5)
        if weak_combos > self.rules['max_weak_combos']:
            return False, f"too_many_weak_combos_{weak_combos}", {}
        
        strong_combos = sum(1 for s in strengths if s >= 0.7)
        if strong_combos < self.rules['min_strong_combos']:
            return False, f"insufficient_strong_combos_{strong_combos}", {}
        
        avg_strength = np.mean(strengths)
        if avg_strength < self.rules['min_avg_strength']:
            return False, f"low_avg_strength_{avg_strength:.2f}", {}
        
        unbeatable_combos = sum(1 for s in strengths if s >= 0.8)
        if unbeatable_combos < self.rules['min_unbeatable_combos']:
            return False, f"no_unbeatable_combos_{unbeatable_combos}", {}
        
        strength_profile = {
            'total_cards': total_cards,
            'avg_strength': avg_strength,
            'strong_combos': strong_combos,
            'unbeatable_combos': unbeatable_combos,
            'strengths': strengths
        }
        
        logger.debug(f"Hand validation passed: {strength_profile}")
        return True, "validation_passed", strength_profile
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """
        Get summary of current rules for debugging/logging
        
        Returns:
            Dictionary with rule descriptions
        """
        return {
            'rules': self.rules,
            'description': {
                'min_total_cards': 'Minimum cards required for valid hand (10)',
                'max_weak_combos': 'Maximum weak combos allowed (strength < 0.5)',
                'min_strong_combos': 'Minimum strong combos required (strength >= 0.7)',
                'min_avg_strength': 'Minimum average strength across all combos',
                'min_unbeatable_combos': 'Minimum unbeatable combos required (strength >= 0.8)'
            }
        }
