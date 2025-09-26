"""
Probability calculation utilities for unbeatable sequences
Extracted from model_build/scripts/unbeatable/unbeatable_sequence_model.py
"""

import numpy as np
import logging
from typing import List, Dict, Any

from ai_common.core.combo_analyzer import ComboAnalyzer

logger = logging.getLogger(__name__)


class UnbeatableProbabilityCalculator:
    """Calculate unbeatable probabilities and model confidence - reusable for evaluation"""
    
    @staticmethod
    def calculate_unbeatable_probability(sequence: List[Dict[str, Any]]) -> float:
        """
        Calculate probability that sequence is unbeatable
        
        Args:
            sequence: List of combo dictionaries
            
        Returns:
            Probability value between 0.0 and 1.0
        """
        if not sequence:
            return 0.0
        
        strengths = [ComboAnalyzer.calculate_combo_strength(combo) for combo in sequence]
        
        # Simple heuristic based on strengths
        avg_strength = np.mean(strengths)
        max_strength = max(strengths)
        strong_count = sum(1 for s in strengths if s >= 0.8)
        
        # Probability calculation
        prob = (avg_strength * 0.4 + max_strength * 0.4 + (strong_count / len(strengths)) * 0.2)
        return min(1.0, max(0.0, prob))
    
    @staticmethod
    def calculate_model_confidence(validation_result: Dict[str, Any], user_patterns: Dict[str, Any]) -> float:
        """
        Calculate overall model confidence
        
        Args:
            validation_result: Result from validation model
            user_patterns: Result from pattern model
            
        Returns:
            Confidence value between 0.0 and 1.0
        """
        validation_conf = validation_result.get('confidence', 0.5)
        pattern_score = user_patterns.get('pattern_score', 0.5)
        
        # Combined confidence
        return (validation_conf + pattern_score) / 2.0
    
    @staticmethod
    def calculate_sequence_stats(sequence: List[Dict[str, Any]], user_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive sequence statistics
        
        Args:
            sequence: List of combo dictionaries
            user_patterns: Result from pattern model
            
        Returns:
            Dictionary with sequence statistics
        """
        if not sequence:
            return {
                'total_cards': 0,
                'avg_strength': 0.0,
                'unbeatable_combos': 0,
                'pattern_used': 'unknown'
            }
        
        strengths = [ComboAnalyzer.calculate_combo_strength(combo) for combo in sequence]
        
        return {
            'total_cards': sum(len(combo.get('cards', [])) for combo in sequence),
            'avg_strength': float(np.mean(strengths)),
            'unbeatable_combos': sum(1 for s in strengths if s >= 0.8),
            'pattern_used': user_patterns.get('sequence_building_preference', 'unknown'),
            'max_strength': float(np.max(strengths)),
            'min_strength': float(np.min(strengths)),
            'strength_variance': float(np.var(strengths))
        }
    
    @staticmethod
    def calculate_hand_strength_profile(combos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate detailed strength profile for hand analysis
        
        Args:
            combos: List of combo dictionaries
            
        Returns:
            Dictionary with strength analysis
        """
        if not combos:
            return {
                'total_combos': 0,
                'total_cards': 0,
                'avg_strength': 0.0,
                'strong_combos': 0,
                'unbeatable_combos': 0,
                'weak_combos': 0,
                'strength_distribution': {}
            }
        
        strengths = [ComboAnalyzer.calculate_combo_strength(combo) for combo in combos]
        
        strong_combos = sum(1 for s in strengths if s >= 0.7)
        unbeatable_combos = sum(1 for s in strengths if s >= 0.8)
        weak_combos = sum(1 for s in strengths if s < 0.5)
        
        # Strength distribution by ranges
        strength_distribution = {
            'very_weak': sum(1 for s in strengths if s < 0.3),
            'weak': sum(1 for s in strengths if 0.3 <= s < 0.5),
            'medium': sum(1 for s in strengths if 0.5 <= s < 0.7),
            'strong': sum(1 for s in strengths if 0.7 <= s < 0.8),
            'unbeatable': sum(1 for s in strengths if s >= 0.8)
        }
        
        return {
            'total_combos': len(combos),
            'total_cards': sum(len(combo.get('cards', [])) for combo in combos),
            'avg_strength': float(np.mean(strengths)),
            'strong_combos': strong_combos,
            'unbeatable_combos': unbeatable_combos,
            'weak_combos': weak_combos,
            'strength_distribution': strength_distribution,
            'strengths': strengths
        }
