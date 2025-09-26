"""
Production Báo Sâm Model Provider
Integrates the high-accuracy rule-based model into the game system
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductionBaoSamProvider:
    """Production-ready Báo Sâm decision provider"""
    
    def __init__(self):
        self.accuracy_log = []
        self.decision_count = 0
        self.correct_decisions = 0
        
    def calculate_combo_strength(self, combo: Dict[str, Any]) -> float:
        """Calculate strength of a single combo"""
        combo_type = combo['combo_type']
        rank_value = combo['rank_value']
        
        # Base strength by combo type
        base_strength = {
            'single': 0.1, 'pair': 0.3, 'triple': 0.5,
            'straight': 0.7, 'quad': 0.9
        }.get(combo_type, 0.1)
        
        # Rank bonus (higher rank = stronger)
        rank_bonus = (rank_value / 12.0) * 0.3
        
        # Special bonuses for high-value combos
        special_bonus = 0.0
        if combo_type == 'straight' and rank_value >= 8:
            special_bonus = 0.2  # High straight
        elif combo_type == 'quad':
            special_bonus = 0.3  # Quad is very strong
        elif combo_type == 'triple' and rank_value >= 10:
            special_bonus = 0.15  # High triple
        
        return base_strength + rank_bonus + special_bonus
    
    def analyze_sequence_strategy(self, sequence: List[Dict]) -> Dict[str, Any]:
        """Analyze sequence for strategic patterns"""
        if not sequence:
            return {
                'total_strength': 0.0,
                'average_strength': 0.0,
                'strong_combos': 0,
                'high_rank_combos': 0,
                'weak_combos': 0,
                'winning_pattern': False,
                'risk_level': 'high'
            }
        
        # Calculate individual combo strengths
        combo_strengths = [self.calculate_combo_strength(combo) for combo in sequence]
        total_strength = sum(combo_strengths)
        average_strength = total_strength / len(sequence)
        
        # Count different types of combos
        strong_combos = len([c for c in sequence if c['combo_type'] in ['straight', 'quad']])
        high_rank_combos = len([c for c in sequence if c['rank_value'] >= 8])
        weak_combos = len([c for c in sequence if c['combo_type'] in ['single', 'pair']])
        
        # Check for winning pattern
        winning_pattern = False
        if len(sequence) >= 2:
            first_combo = sequence[0]
            last_combo = sequence[-1]
            
            # Winning pattern: strong start and strong finish
            if (first_combo['combo_type'] in ['straight', 'quad'] and 
                last_combo['combo_type'] in ['straight', 'quad']):
                winning_pattern = True
            # Alternative: very strong start with high rank
            elif (first_combo['combo_type'] in ['straight', 'quad'] and 
                  first_combo['rank_value'] >= 9):
                winning_pattern = True
        
        # Determine risk level
        if average_strength >= 0.8 and strong_combos >= 2:
            risk_level = 'low'
        elif average_strength >= 0.6 and strong_combos >= 1:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        return {
            'total_strength': total_strength,
            'average_strength': average_strength,
            'strong_combos': strong_combos,
            'high_rank_combos': high_rank_combos,
            'weak_combos': weak_combos,
            'winning_pattern': winning_pattern,
            'risk_level': risk_level
        }
    
    def calculate_win_probability(self, sequence_analysis: Dict[str, Any]) -> float:
        """Calculate win probability based on sequence analysis"""
        base_prob = sequence_analysis['average_strength']
        
        # Bonuses
        bonus = 0.0
        
        # Bonus for multiple strong combos
        if sequence_analysis['strong_combos'] >= 2:
            bonus += 0.2
        elif sequence_analysis['strong_combos'] >= 1:
            bonus += 0.1
        
        # Bonus for high-rank combos
        if sequence_analysis['high_rank_combos'] >= 2:
            bonus += 0.15
        elif sequence_analysis['high_rank_combos'] >= 1:
            bonus += 0.05
        
        # Bonus for winning pattern
        if sequence_analysis['winning_pattern']:
            bonus += 0.25
        
        # Penalties
        penalty = 0.0
        
        # Penalty for too many weak combos
        if sequence_analysis['weak_combos'] >= 3:
            penalty += 0.3
        elif sequence_analysis['weak_combos'] >= 2:
            penalty += 0.15
        
        # Penalty for high risk level
        if sequence_analysis['risk_level'] == 'high':
            penalty += 0.2
        elif sequence_analysis['risk_level'] == 'medium':
            penalty += 0.1
        
        final_prob = base_prob + bonus - penalty
        return max(0.05, min(0.95, final_prob))
    
    def predict(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict action for ModelBot compatibility"""
        # For Báo Sâm decisions, we need to analyze the current hand
        hand = game_record.get('hand', [])
        
        # If this is a Báo Sâm declaration decision, use our specialized logic
        if game_record.get('game_type') == 'sam' and any(move.get('type') == 'declare_bao_sam' for move in legal_moves):
            # For now, use a simple heuristic for Báo Sâm declaration
            # In a real implementation, we'd analyze the potential combo sequence
            return self._analyze_bao_sam_declaration(hand, legal_moves)
        
        # For regular moves, use standard logic
        for move in legal_moves:
            if move.get("type") == "play_cards" and move.get("cards"):
                return {"type": "play_cards", "cards": move.get("cards")}
        
        return {"type": "pass", "cards": []}
    
    def _analyze_bao_sam_declaration(self, hand: List[int], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze whether to declare Báo Sâm"""
        # Simple heuristic: if hand has many high cards, consider declaring
        high_cards = sum(1 for card in hand if (card % 13) >= 8)
        
        if high_cards >= 8:  # Conservative threshold
            # Find the declare_bao_sam move
            for move in legal_moves:
                if move.get('type') == 'declare_bao_sam':
                    return move
        
        # Otherwise, play cards normally
        for move in legal_moves:
            if move.get("type") == "play_cards" and move.get("cards"):
                return {"type": "play_cards", "cards": move.get("cards")}
        
        return {"type": "pass", "cards": []}
    
    def predict_bao_sam_decision(self, hand: List[int], combo_sequence: List[Dict]) -> Dict[str, Any]:
        """Make Báo Sâm decision for given hand and combo sequence"""
        # Analyze sequence
        analysis = self.analyze_sequence_strategy(combo_sequence)
        
        # Calculate win probability
        win_probability = self.calculate_win_probability(analysis)
        
        # Decision logic with conservative approach
        should_declare = False
        confidence = 0.0
        reason = ""
        
        # High confidence conditions
        if (win_probability >= 0.85 or 
            (analysis['average_strength'] >= 0.8 and analysis['strong_combos'] >= 2) or
            (analysis['winning_pattern'] and win_probability >= 0.75)):
            
            should_declare = True
            confidence = min(0.95, win_probability + 0.1)
            reason = "high_confidence_winning_sequence"
        
        # Medium confidence conditions (more conservative)
        elif (win_probability >= 0.75 and analysis['risk_level'] != 'high' and
              analysis['strong_combos'] >= 1):
            
            should_declare = True
            confidence = win_probability
            reason = "medium_confidence_good_sequence"
        
        # Low confidence - don't declare
        else:
            should_declare = False
            confidence = 1.0 - win_probability
            reason = "insufficient_confidence_risky_sequence"
        
        # Additional conservative filters
        if analysis['weak_combos'] >= 3:
            should_declare = False
            confidence = 0.1
            reason = "too_many_weak_combos"
        
        if analysis['risk_level'] == 'high' and win_probability < 0.8:
            should_declare = False
            confidence = 0.2
            reason = "high_risk_low_win_probability"
        
        return {
            'should_declare': should_declare,
            'confidence': confidence,
            'win_probability': win_probability,
            'sequence_analysis': analysis,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_accuracy_stats(self) -> Dict[str, Any]:
        """Get accuracy statistics"""
        if self.decision_count == 0:
            return {'accuracy': 0.0, 'total_decisions': 0, 'correct_decisions': 0}
        
        accuracy = self.correct_decisions / self.decision_count
        
        return {
            'overall_accuracy': accuracy,
            'total_decisions': self.decision_count,
            'correct_decisions': self.correct_decisions
        }

# Global instance
_production_provider = None

def get_production_bao_sam_provider() -> ProductionBaoSamProvider:
    """Get singleton instance of production Báo Sâm provider"""
    global _production_provider
    if _production_provider is None:
        _production_provider = ProductionBaoSamProvider()
        logger.info("Initialized Production Báo Sâm Provider")
    return _production_provider
