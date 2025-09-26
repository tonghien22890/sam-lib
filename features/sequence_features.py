"""
Feature extraction for ML models
Extracted from model_build/scripts/unbeatable/unbeatable_sequence_model.py
"""

import numpy as np
import logging
from typing import List, Dict, Any

from ai_common.core.combo_analyzer import ComboAnalyzer

logger = logging.getLogger(__name__)


class SequenceFeatureExtractor:
    """Feature extraction utilities for ML models - reusable for training"""
    
    @staticmethod
    def extract_combo_features(combo: Dict[str, Any]) -> List[float]:
        """
        Extract combo-level features for ML models
        
        Args:
            combo: Combo dictionary with combo_type, rank_value, cards
            
        Returns:
            List of normalized feature values
        """
        features = []
        
        # Basic properties
        combo_types = ['single', 'pair', 'triple', 'straight', 'quad']
        combo_type = combo['combo_type']
        for ct in combo_types:
            features.append(1.0 if ct == combo_type else 0.0)
        
        # Rank normalized
        rank_value = combo.get('rank_value', 0)
        features.append(rank_value / 12.0)
        
        # Absolute strength
        strength = ComboAnalyzer.calculate_combo_strength(combo)
        features.append(strength)
        
        # Card count
        card_count = len(combo.get('cards', []))
        features.append(card_count / 10.0)  # Normalize by max possible
        
        return features
    
    @staticmethod
    def extract_sequence_features(combos: List[Dict[str, Any]]) -> List[float]:
        """
        Extract sequence-level features for ML models
        
        Args:
            combos: List of combo dictionaries
            
        Returns:
            List of normalized feature values
        """
        if not combos:
            return [0.0] * 10
        
        strengths = [ComboAnalyzer.calculate_combo_strength(combo) for combo in combos]
        
        features = []
        
        # Strength distribution
        features.append(np.mean(strengths))  # avg_strength
        features.append(np.var(strengths))   # strength_variance
        features.append(max(strengths) - min(strengths))  # strength_range
        
        # Combo distribution
        combo_types = ['single', 'pair', 'triple', 'straight', 'quad']
        type_counts = [sum(1 for c in combos if c['combo_type'] == ct) for ct in combo_types]
        total_combos = len(combos)
        type_distribution = [count / total_combos for count in type_counts]
        features.extend(type_distribution)
        
        # Power indicators
        power_combo_ratio = sum(1 for s in strengths if s >= 0.8) / len(strengths)
        features.append(power_combo_ratio)
        
        # Coverage efficiency
        total_cards = sum(len(combo.get('cards', [])) for combo in combos)
        features.append(total_cards / 10.0)  # Should be 1.0 for valid hands
        
        return features
    
    @staticmethod
    def extract_pattern_features(hand_data: Dict[str, Any]) -> List[float]:
        """
        Extract features for pattern learning
        
        Args:
            hand_data: Dictionary with hand, player_count, possible_combos
            
        Returns:
            List of normalized feature values
        """
        combos = hand_data.get('possible_combos', [])
        
        if not combos:
            return [0.0] * 15
        
        strengths = [ComboAnalyzer.calculate_combo_strength(combo) for combo in combos]
        
        features = []
        
        # Combo diversity
        combo_types = set(combo['combo_type'] for combo in combos)
        combo_diversity = len(combo_types) / 5.0  # Max 5 types
        features.append(combo_diversity)
        
        # Power concentration
        power_combos = sum(1 for s in strengths if s >= 0.8)
        power_concentration = power_combos / len(combos)
        features.append(power_concentration)
        
        # Balance preference
        strength_variance = np.var(strengths)
        features.append(strength_variance)
        
        # Type preferences
        combo_types_list = ['single', 'pair', 'triple', 'straight', 'quad']
        type_counts = [sum(1 for c in combos if c['combo_type'] == ct) for ct in combo_types_list]
        total_combos = len(combos)
        type_prefs = [count / total_combos for count in type_counts]
        features.extend(type_prefs)
        
        # Strength distribution
        features.extend([
            np.mean(strengths),
            np.max(strengths),
            np.min(strengths),
            np.median(strengths)
        ])
        
        # Additional pattern signals to reach 15 features
        # Ratio of singles and pairs (indicates weakness pattern)
        singles_ratio = sum(1 for c in combos if c['combo_type'] == 'single') / total_combos
        pairs_ratio = sum(1 for c in combos if c['combo_type'] == 'pair') / total_combos
        features.extend([singles_ratio, pairs_ratio])
        
        # Context
        player_count = hand_data.get('player_count', 4)
        features.append(player_count / 4.0)
        
        return features
    
    @staticmethod
    def extract_validation_features(hand_data: Dict[str, Any]) -> List[float]:
        """
        Extract all features for validation model
        
        Args:
            hand_data: Dictionary with hand, player_count, possible_combos
            
        Returns:
            List of normalized feature values
        """
        combos = hand_data.get('possible_combos', [])
        
        features = []
        
        # Sequence-level features
        seq_features = SequenceFeatureExtractor.extract_sequence_features(combos)
        features.extend(seq_features)
        
        # First 3 combo features
        for i in range(3):
            if i < len(combos):
                combo_features = SequenceFeatureExtractor.extract_combo_features(combos[i])
                features.extend(combo_features)
            else:
                # Pad with zeros
                features.extend([0.0] * 8)  # 8 combo features
        
        # Context features
        player_count = hand_data.get('player_count', 4)
        features.append(player_count / 4.0)  # Normalize
        
        return features
    
    @staticmethod
    def extract_threshold_features(hand_data: Dict[str, Any], user_patterns: Dict[str, Any]) -> List[float]:
        """
        Extract features for threshold learning
        
        Args:
            hand_data: Dictionary with hand, player_count, possible_combos
            user_patterns: Dictionary with user pattern information
            
        Returns:
            List of normalized feature values
        """
        features = []
        
        # Hand characteristics
        combos = hand_data.get('possible_combos', [])
        if combos:
            strengths = [ComboAnalyzer.calculate_combo_strength(combo) for combo in combos]
            
            features.extend([
                np.mean(strengths),
                np.max(strengths),
                len(combos),
                sum(1 for s in strengths if s >= 0.8)  # unbeatable combos
            ])
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])
        
        # User patterns
        patterns = user_patterns.get('combo_patterns', {})
        features.extend([
            patterns.get('power_concentration', 0.5),
            patterns.get('combo_diversity', 0.5),
            patterns.get('balance_preference', 0.5)
        ])
        
        # Context
        player_count = hand_data.get('player_count', 4)
        features.append(player_count / 4.0)
        
        return features
