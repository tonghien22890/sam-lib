#!/usr/bin/env python3
"""
Sequence Evaluator - Rule-based top-k sequence evaluation
Evaluates top sequences from a hand using beam search and rule-based scoring
"""

import itertools
from typing import List, Dict, Any, Tuple, Set, Optional
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
    
    def __init__(self, enforce_full_coverage: bool = True):
        self.combo_analyzer = ComboAnalyzer()
        self.enforce_full_coverage = enforce_full_coverage
        
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

        # Prepare card availability map
        rank_to_cards = self._build_rank_to_cards(hand)
        
        # Find all possible combos from hand
        all_combos = self._find_all_combos(rank_to_cards)
        
        # Use beam search to find top sequences
        sequences = self._beam_search_sequences(all_combos, rank_to_cards, beam_size)
        
        # Score and rank sequences
        scored_sequences = []
        for sequence in sequences:
            score = self._score_sequence(sequence, hand, enforce_full_coverage)
            combo_count = len(score['sequence'])
            avg_strength = score['total_strength'] / max(1, combo_count)
            
            ordered_sequence = self._order_sequence(score['sequence'])
            
            scored_sequences.append({
                'sequence': ordered_sequence,
                'total_strength': score['total_strength'],
                'coverage_score': score['coverage_score'],
                'end_rule_compliance': score['end_rule_compliance'],
                'used_cards': score['used_cards'],
                'combo_count': combo_count,
                'avg_combo_strength': avg_strength
            })
        
        # Sort by average combo strength (descending) - prefer fewer, stronger combos
        scored_sequences.sort(key=lambda x: x['avg_combo_strength'], reverse=True)
        
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
    
    def _build_rank_to_cards(self, hand: List[int]) -> Dict[int, List[int]]:
        rank_to_cards: Dict[int, List[int]] = {}
        for card in sorted(hand):
            rank = card % 13
            rank_to_cards.setdefault(rank, []).append(card)
        return rank_to_cards
    
    def _find_all_combos(self, rank_to_cards: Dict[int, List[int]]) -> List[Dict[str, Any]]:
        """Find ALL possible combos from hand (not just greedy optimal)"""
        combos = []
        
        # Generate singles, pairs, triples, four_kinds from each rank
        for rank, cards in rank_to_cards.items():
            # Singles
            for card in cards:
                card_ranks = [rank]
                combos.append({
                    'type': 'single',
                    'rank_value': rank,
                    'cards': card_ranks,
                    'strength': self._calculate_strength_from_ranks('single', rank, card_ranks, rank_to_cards)
                })
            
            # Pairs
            if len(cards) >= 2:
                card_ranks = [rank, rank]
                combos.append({
                    'type': 'pair',
                    'rank_value': rank,
                    'cards': card_ranks,
                    'strength': self._calculate_strength_from_ranks('pair', rank, card_ranks, rank_to_cards)
                })
            
            # Triples
            if len(cards) >= 3:
                card_ranks = [rank, rank, rank]
                combos.append({
                    'type': 'triple',
                    'rank_value': rank,
                    'cards': card_ranks,
                    'strength': self._calculate_strength_from_ranks('triple', rank, card_ranks, rank_to_cards)
                })
            
            # Four of a kind
            if len(cards) >= 4:
                card_ranks = [rank, rank, rank, rank]
                combos.append({
                    'type': 'four_kind',
                    'rank_value': rank,
                    'cards': card_ranks,
                    'strength': self._calculate_strength_from_ranks('four_kind', rank, card_ranks, rank_to_cards)
                })
        
        # Generate all possible straights (3+ consecutive ranks, allowing wrap-around)
        combos.extend(self._generate_straight_combos(rank_to_cards))
        
        # Generate all possible double_seqs (3+ consecutive pairs)
        pair_ranks = sorted([r for r, cards in rank_to_cards.items() if len(cards) >= 2])
        for length in range(3, len(pair_ranks) + 1):
            for start_idx in range(len(pair_ranks) - length + 1):
                window = pair_ranks[start_idx:start_idx + length]
                
                # Check if consecutive
                if all(window[i+1] - window[i] == 1 for i in range(len(window) - 1)):
                    double_seq_cards = []
                    for r in window:
                        double_seq_cards.extend([r, r])
                    
                    combos.append({
                        'type': 'double_seq',
                        'rank_value': window[0],
                        'cards': double_seq_cards,
                        'strength': self._calculate_strength_from_ranks('double_seq', window[0], double_seq_cards, rank_to_cards)
                    })
        
        return combos
    
    def _generate_straight_combos(self, rank_to_cards: Dict[int, List[int]]) -> List[Dict[str, Any]]:
        combos: List[Dict[str, Any]] = []
        ranks = sorted(rank_to_cards.keys())
        if not ranks:
            return combos
        
        extended = ranks + [r + 13 for r in ranks if r < 12]
        seen: Set[Tuple[int, ...]] = set()
        
        for i in range(len(extended)):
            start = extended[i]
            last = start - 1
            window: List[int] = []
            for j in range(i, len(extended)):
                current = extended[j]
                if current != last + 1:
                    break
                if current - start > 12:
                    break
                actual_rank = current % 13
                if actual_rank not in rank_to_cards:
                    break
                window.append(actual_rank)
                last = current
                
                if len(window) >= 3:
                    signature = tuple(window)
                    if 12 in signature and 0 not in signature:
                        continue
                    if signature in seen:
                        continue
                    seen.add(signature)
                    combos.append({
                        'type': 'straight',
                        'rank_value': signature[0],
                        'cards': list(signature),
                        'strength': self._calculate_strength_from_ranks('straight', signature[0], list(signature), rank_to_cards)
                    })
        return combos
    
    def _order_sequence(self, sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not sequence:
            return sequence
        
        seq = sorted(sequence, key=lambda c: c.get('strength', 0.0))
        strengths = [c.get('strength', 0.0) for c in seq]
        second_weakest = strengths[1] if len(strengths) > 1 else strengths[0]
        
        if second_weakest <= 0.5:
            return seq  # keep weak→strong
        
        weakest = seq.pop(0) if seq else None
        strongest = seq.pop(-1) if seq else None
        ordered = seq  # already sorted weak→strong
        if strongest is not None:
            ordered.append(strongest)
        if weakest is not None:
            ordered.append(weakest)
        return ordered
    
    def _calculate_strength_from_ranks(self, combo_type: str, rank_value: int, card_ranks: List[int], rank_to_cards: Dict[int, List[int]]) -> float:
        sample_cards = self._sample_cards_from_ranks(card_ranks, rank_to_cards)
        if not sample_cards:
            return 0.0
        combo_payload = {
            'combo_type': combo_type,
            'rank_value': rank_value,
            'cards': sample_cards
        }
        return self.combo_analyzer.calculate_combo_strength(combo_payload)
    
    def _sample_cards_from_ranks(self, card_ranks: List[int], rank_to_cards: Dict[int, List[int]]) -> List[int]:
        temp_usage: Dict[int, int] = {}
        taken: List[int] = []
        for rank in card_ranks:
            usage = temp_usage.get(rank, 0)
            cards = rank_to_cards.get(rank, [])
            if usage >= len(cards):
                return []
            taken.append(cards[usage])
            temp_usage[rank] = usage + 1
        return taken
    
    def _beam_search_sequences(self, combos: List[Dict[str, Any]], rank_to_cards: Dict[int, List[int]], beam_size: int) -> List[List[Dict[str, Any]]]:
        """Generate top sequences using priority-guided greedy construction"""
        if not combos:
            return []
        
        top_sequences: List[List[Dict[str, Any]]] = []
        seen_signatures = set()
        
        # Sort combos by priority and intrinsic strength
        sorted_combos = sorted(
            combos,
            key=lambda c: (
                self._combo_priority(c.get('type')),
                c.get('strength', 0.0),
                len(c.get('cards', []))
            ),
            reverse=True
        )
        
        top_avg_threshold = 0.0
        
        for start_combo in sorted_combos:
            start_strength = start_combo.get('strength', 0.0)
            if len(top_sequences) >= beam_size and start_strength <= top_avg_threshold:
                break
            
            sequence = self._build_sequence_from_start(start_combo, sorted_combos, rank_to_cards)
            if not sequence:
                continue
            
            signature = tuple(sorted(
                (c.get('type'), c.get('rank_value'), len(c.get('cards', [])))
                for c in sequence
            ))
            if signature in seen_signatures:
                continue
            
            seen_signatures.add(signature)
            top_sequences.append(self._order_sequence(sequence))
            
            if len(top_sequences) >= beam_size:
                # Estimate avg strength for thresholding using raw strengths
                scored = sorted(
                    (
                        sum(c.get('strength', 0.0) for c in seq) / max(1, len(seq)),
                        seq
                    )
                    for seq in top_sequences
                )
                top_sequences = [seq for _, seq in scored[-beam_size:]]
                top_avg_threshold = scored[-beam_size][0]
        
        return top_sequences
    
    def _combo_priority(self, combo_type: str) -> int:
        priority_map = {
            'four_kind': 6,
            'double_seq': 5,
            'straight': 4,
            'triple': 3,
            'pair': 2,
            'single': 1,
            'pass': 0
        }
        return priority_map.get(combo_type or 'single', 1)
    
    def _build_sequence_from_start(self, start_combo: Dict[str, Any], sorted_combos: List[Dict[str, Any]], rank_to_cards: Dict[int, List[int]]) -> List[Dict[str, Any]]:
        available = {rank: list(cards) for rank, cards in rank_to_cards.items()}
        
        start_cards = self._consume_cards_for_combo(start_combo, available)
        if start_cards is None:
            return []
        
        sequence = [self._with_cards(start_combo, start_cards)]
        
        for combo in sorted_combos:
            if combo is start_combo:
                continue
            combo_cards = self._consume_cards_for_combo(combo, available)
            if combo_cards is None:
                continue
            sequence.append(self._with_cards(combo, combo_cards))
        
        return self._order_sequence(sequence)
    
    def _consume_cards_for_combo(self, combo: Dict[str, Any], available: Dict[int, List[int]]) -> Optional[List[int]]:
        card_ranks = combo.get('cards', [])
        if not card_ranks:
            return []
        
        demand: Dict[int, int] = {}
        for rank in card_ranks:
            demand[rank] = demand.get(rank, 0) + 1
        
        for rank, count in demand.items():
            if len(available.get(rank, [])) < count:
                return None
        
        taken: List[int] = []
        for rank in card_ranks:
            pool = available.get(rank, [])
            chosen = pool.pop()
            taken.append(chosen)
        
        return taken
    
    def _with_cards(self, combo: Dict[str, Any], cards: List[int]) -> Dict[str, Any]:
        new_combo = dict(combo)
        new_combo['cards'] = cards
        return new_combo
    
    def _score_sequence(self, sequence: List[Dict[str, Any]], hand: List[int], enforce_full_coverage: bool) -> Dict[str, Any]:
        """Score a sequence and optionally extend to full coverage"""
        if not sequence:
            return {
                'sequence': [],
                'total_strength': 0.0,
                'coverage_score': 0.0,
                'end_rule_compliance': True,
                'used_cards': set()
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

        # Calculate total strength (sum of all combo strengths)
        total_strength = sum(combo['strength'] for combo in extended_sequence)

        # Check end rule compliance (not ending with 2 or quad)
        last_combo = extended_sequence[-1]
        end_rule_compliance = not (
            (last_combo['rank_value'] == 12) or  # Not ending with 2
            (last_combo['type'] == 'four_kind')       # Not ending with quad
        )
        
        return {
            'sequence': extended_sequence,
            'total_strength': total_strength,
            'coverage_score': coverage_score,
            'end_rule_compliance': end_rule_compliance,
            'used_cards': used_cards
        }

    def _build_cleanup_from_remaining(self, remaining_cards: List[int]) -> List[Dict[str, Any]]:
        """Build cleanup combos from remaining cards (pairs + singles)"""
        # Group by rank
        rank_to_cards = {}
        for c in remaining_cards:
            r = c % 13
            rank_to_cards.setdefault(r, []).append(c)

        combos = []
        
        # Create pairs first
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
