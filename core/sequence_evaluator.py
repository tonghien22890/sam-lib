#!/usr/bin/env python3
"""
Sequence Evaluator - Rule-based top-k sequence evaluation
Evaluates top sequences from a hand using beam search and rule-based scoring
"""

import itertools
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import sys
import os

# Add project root to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_common.core.combo_analyzer import ComboAnalyzer


class SequenceEvaluator:
    """
    Rule-based sequence evaluator that finds top-k strongest sequences from a hand
    """
    
    def __init__(self, enforce_full_coverage: bool = True, coverage_weight: float = 0.25):
        self.combo_analyzer = ComboAnalyzer()
        self.combo_types = ['single', 'pair', 'triple', 'quad', 'straight', 'double_seq']
        # If true, extend sequences with planned cleanup (pairs then singles) so they cover the entire hand
        self.enforce_full_coverage = enforce_full_coverage
        # Weight to reward higher coverage in the scoring function (applies even if not strictly enforced)
        self.coverage_weight = coverage_weight
        # Weight to reward weak→strong ordering inside the plan (0-0.5 reasonable)
        self.order_weight = float(os.environ.get('SEQ_ORDER_WEIGHT', '0.15')) if 'os' in globals() else 0.15
        
    def evaluate_top_sequences(self, hand: List[int], k: int = 3, beam_size: int = 50, enforce_full_coverage: bool = None) -> List[Dict[str, Any]]:
        """
        Find top-k sequences from hand using beam search
        
        Args:
            hand: List of card IDs (0-51)
            k: Number of top sequences to return
            beam_size: Beam search width
            
        Returns:
            List of sequence dicts with:
            - sequence: List[combo_dicts] (ordered by strength)
            - total_strength: float
            - coverage_score: float (how well it covers hand)
            - end_rule_compliance: bool (not ending with 2/quad)
            - used_cards: Set of card IDs used
        """
        if not hand:
            return []
            
        # Determine enforcement flag
        if enforce_full_coverage is None:
            enforce_full_coverage = self.enforce_full_coverage

        # Find all possible combos from hand
        all_combos = self._find_all_combos(hand)
        
        # Use beam search to find top sequences
        sequences = self._beam_search_sequences(all_combos, hand, beam_size)
        
        # Score and rank sequences
        scored_sequences = []
        for sequence in sequences:
            score = self._score_sequence(sequence, hand, enforce_full_coverage)
            scored_sequences.append({
                'sequence': score['sequence'],
                'total_strength': score['total_strength'],
                'coverage_score': score['coverage_score'],
                'end_rule_compliance': score['end_rule_compliance'],
                'used_cards': score['used_cards'],
                'combo_count': len(score['sequence']),
                'avg_combo_strength': score['total_strength'] / max(1, len(score['sequence']))
            })
        
        # Sort by total strength (descending)
        scored_sequences.sort(key=lambda x: x['total_strength'], reverse=True)
        
        topk = scored_sequences[:k]

        # Optional debug logging
        try:
            import os
            if os.environ.get('SEQ_DEBUG', '0') == '1':
                print(f"[SEQ_DEBUG] Hand size={len(hand)} candidates={len(topk)} (enforce_full_coverage={enforce_full_coverage})")
                for idx, item in enumerate(topk):
                    seq = item['sequence']
                    combos_view = [
                        {
                            'i': i,
                            't': c.get('type'),
                            'r': c.get('rank_value'),
                            'len': len(c.get('cards', [])),
                            's': round(c.get('strength', 0.0), 3)
                        } for i, c in enumerate(seq)
                    ]
                    print(f"[SEQ_DEBUG] #{idx+1} total={item['total_strength']:.3f} cov={item['coverage_score']:.2f} avg={item['avg_combo_strength']:.3f} combos={len(seq)}")
                    print(f"[SEQ_DEBUG]      {combos_view}")
        except Exception:
            pass

        return topk
    
    def _find_all_combos(self, hand: List[int]) -> List[Dict[str, Any]]:
        """Find all possible combos from hand using ComboAnalyzer (supports long straights)"""
        # Use ComboAnalyzer to get all combos (including long straights 3-10 cards)
        raw_combos = self.combo_analyzer.analyze_hand(hand)
        
        # Convert to our format and add strength
        combos = []
        for combo in raw_combos:
            combos.append({
                'type': combo['combo_type'],
                'rank_value': combo['rank_value'],
                'cards': combo['cards'],
                'strength': self.combo_analyzer.calculate_combo_strength(combo)
            })
        
        return combos
    
    def _beam_search_sequences(self, combos: List[Dict[str, Any]], hand: List[int], beam_size: int) -> List[List[Dict[str, Any]]]:
        """Use beam search to find top sequences"""
        if not combos:
            return []
        
        # Prefer exploring weaker combos first to encourage weak→strong ordering
        combos.sort(key=lambda x: x['strength'])
        
        # Initialize beam with empty sequences
        beam = [{'sequence': [], 'used_cards': set(), 'remaining_cards': set(hand)}]
        
        for _ in range(min(len(combos), 10)):  # Limit depth to avoid explosion
            new_beam = []
            
            for state in beam:
                remaining_cards = state['remaining_cards']
                
                # Try adding each combo that doesn't conflict
                for combo in combos:
                    combo_cards = set(combo['cards'])
                    
                    # Check if combo can be added (no card conflicts)
                    if combo_cards.issubset(remaining_cards):
                        new_sequence = state['sequence'] + [combo]
                        new_used_cards = state['used_cards'] | combo_cards
                        new_remaining = remaining_cards - combo_cards
                        
                        new_beam.append({
                            'sequence': new_sequence,
                            'used_cards': new_used_cards,
                            'remaining_cards': new_remaining
                        })
                
                # Also keep the current state (don't add any combo)
                new_beam.append(state)
            
            # Keep top beam_size sequences by order-aware, coverage-aware average strength
            def partial_score(state):
                seq = state['sequence']
                if not seq:
                    return 0.0
                avg = sum(c['strength'] for c in seq) / len(seq)
                # partial coverage
                cov = (len(state['used_cards']) / len(hand)) if hand else 0.0
                # order compliance on partial
                strengths = [c.get('strength', 0.0) for c in seq]
                good = sum(1 for i in range(len(strengths)-1) if strengths[i] <= strengths[i+1] + 1e-9)
                pairs = max(1, len(strengths) - 1)
                order = good / pairs
                score = avg * (1.0 + self.coverage_weight * cov) * (1.0 + self.order_weight * (order - 0.5))
                return score

            new_beam.sort(key=partial_score, reverse=True)
            beam = new_beam[:beam_size]
        
        # Return just the sequences
        return [state['sequence'] for state in beam if state['sequence']]
    
    def _score_sequence(self, sequence: List[Dict[str, Any]], hand: List[int], enforce_full_coverage: bool) -> Dict[str, Any]:
        """Score a sequence. Optionally extend it to full coverage and score the full plan."""
        if not sequence:
            return {
                'sequence': [],
                'total_strength': 0.0,
                'coverage_score': 0.0,
                'end_rule_compliance': True,
                'used_cards': set(),
                'order_compliance': 0.0
            }
        
        # Calculate used cards
        used_cards = set()
        for combo in sequence:
            used_cards.update(combo['cards'])
        coverage_score = len(used_cards) / len(hand) if hand else 0.0

        # Optionally extend with cleanup to ensure full coverage
        extended_sequence = list(sequence)
        if enforce_full_coverage and hand:
            remaining = [c for c in hand if c not in used_cards]
            if remaining:
                cleanup = self._build_cleanup_from_remaining(remaining)
                extended_sequence = sequence + cleanup
                # Recompute used/coverage
                used_cards = set(used_cards)
                for combo in cleanup:
                    used_cards.update(combo['cards'])
                coverage_score = len(used_cards) / len(hand)
        
        # Optionally force a deterministic weak→strong order for the final plan
        try:
            import os
            force_weak_first = os.environ.get('SEQ_FORCE_WEAK_FIRST', '0') == '1'
        except Exception:
            force_weak_first = False

        if force_weak_first and extended_sequence:
            extended_sequence = sorted(extended_sequence, key=lambda c: c.get('strength', 0.0))

        # Calculate average strength over the PLAN we present (extended if needed)
        total_strength = sum(combo['strength'] for combo in extended_sequence) / max(1, len(extended_sequence))

        # Apply a small reward for coverage
        total_strength = total_strength * (1.0 + self.coverage_weight * coverage_score)

        # Order compliance bonus: prefer weak→strong progression
        strengths = [c.get('strength', 0.0) for c in extended_sequence]
        order_pairs = 0
        good_pairs = 0
        for i in range(len(strengths) - 1):
            order_pairs += 1
            if strengths[i] <= strengths[i + 1] + 1e-9:
                good_pairs += 1
        order_compliance = (good_pairs / order_pairs) if order_pairs > 0 else 1.0
        total_strength = total_strength * (1.0 + self.order_weight * (order_compliance - 0.5))

        # Check end rule compliance (not ending with 2 or quad)
        last_combo = extended_sequence[-1]
        end_rule_compliance = not (
            (last_combo['rank_value'] == 12) or  # Not ending with 2
            (last_combo['type'] == 'quad')       # Not ending with quad
        )
        
        return {
            'sequence': extended_sequence,
            'total_strength': total_strength,
            'coverage_score': coverage_score,
            'end_rule_compliance': end_rule_compliance,
            'used_cards': used_cards,
            'order_compliance': order_compliance
        }

    def _build_cleanup_from_remaining(self, remaining_cards: List[int]) -> List[Dict[str, Any]]:
        """Build planned cleanup from remaining cards.
        Strategy: collect pairs and singles, then globally sort by strength ascending (weak→strong)
        so singles are not always pushed to the end.
        """
        # Group by rank
        rank_to_cards = {}
        for c in remaining_cards:
            r = c % 13
            rank_to_cards.setdefault(r, []).append(c)

        combos: List[Dict[str, Any]] = []
        # Create candidate pairs
        for r, cards in rank_to_cards.items():
            if len(cards) >= 2:
                pair_cards = cards[:2]
                combos.append({
                    'type': 'pair',
                    'rank_value': r,
                    'cards': pair_cards,
                    'strength': self.combo_analyzer.calculate_combo_strength({
                        'combo_type': 'pair', 'rank_value': r, 'cards': pair_cards
                    })
                })
                rank_to_cards[r] = cards[2:]

        # Create singles from leftovers
        for r, cards in rank_to_cards.items():
            for c in cards:
                combos.append({
                    'type': 'single',
                    'rank_value': r,
                    'cards': [c],
                    'strength': self.combo_analyzer.calculate_combo_strength({
                        'combo_type': 'single', 'rank_value': r, 'cards': [c]
                    })
                })

        # Global weak→strong ordering across both pairs and singles
        combos.sort(key=lambda x: x.get('strength', 0.0))

        return combos
    
    def get_sequence_summary(self, sequences: List[Dict[str, Any]]) -> str:
        """Get human-readable summary of sequences"""
        if not sequences:
            return "No sequences found"
        
        summary = f"Top {len(sequences)} sequences:\n"
        
        for i, seq_data in enumerate(sequences):
            sequence = seq_data['sequence']
            total_strength = seq_data['total_strength']
            coverage = seq_data['coverage_score']
            compliance = seq_data['end_rule_compliance']
            
            summary += f"\n{i+1}. Strength: {total_strength:.3f}, Coverage: {coverage:.2f}, End Rule OK: {compliance}\n"
            
            for j, combo in enumerate(sequence):
                combo_type = combo['type']
                rank_value = combo['rank_value']
                strength = combo['strength']
                cards = combo['cards']
                summary += f"   {j+1}. {combo_type} rank={rank_value} strength={strength:.3f} cards={cards}\n"
        
        return summary
