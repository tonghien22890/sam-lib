"""
Core combo analysis logic for card games
Extracted from model_build/scripts/unbeatable/unbeatable_sequence_model.py
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ComboAnalyzer:
    """Core combo analysis logic - reusable for different card games"""
    
    @staticmethod
    def analyze_hand(hand: List[int]) -> List[Dict[str, Any]]:
        """
        Analyze hand and find possible combos
        
        Strategy:
        1) Prefer detect straights (3-10 cards) greedily from available ranks
        2) Then detect quads, triples, pairs
        3) Remaining as singles
        All detections consume cards to avoid duplicates across combos
        
        Args:
            hand: List of card indices (0-51)
            
        Returns:
            List of combo dictionaries with combo_type, rank_value, cards
        """
        # Build rank -> list(cards) map
        rank_to_cards: Dict[int, List[int]] = {}
        for card in sorted(hand):
            rank = card % 13
            rank_to_cards.setdefault(rank, []).append(card)

        combos: List[Dict[str, Any]] = []

        # Helper to get available ranks snapshot
        def available_ranks() -> List[int]:
            return sorted([r for r, cards in rank_to_cards.items() if len(cards) > 0])

        # Detect straights greedily (longest runs first)
        while True:
            # In Sam, rank 12 (the 2) is NOT part of straights -> exclude it
            ranks = [r for r in available_ranks() if r != 12]
            if not ranks:
                break

            # Find longest consecutive run from current availability
            best_start = None
            best_len = 0
            i = 0
            while i < len(ranks):
                j = i
                while j + 1 < len(ranks) and ranks[j + 1] == ranks[j] + 1:
                    j += 1
                run_len = j - i + 1
                if run_len > best_len:
                    best_len = run_len
                    best_start = ranks[i]
                i = j + 1

            # Only create straights of length >= 3 (prefer 5+)
            if best_len < 3:
                break

            # Build the straight from best_start with best_len, but cap at 10 (no wrap, no rank 12)
            start = best_start
            end = best_start + best_len - 1
            length = best_len

            # Prefer taking 10..5 length by trimming from ends if needed to hit max 10
            if length > 10:
                length = 10
                end = start + length - 1

            # Consume one card per rank for the straight
            straight_cards: List[int] = []
            for r in range(start, end + 1):
                if r in rank_to_cards and rank_to_cards[r]:
                    straight_cards.append(rank_to_cards[r].pop(0))

            # Validate minimum usable length (after consumption some ranks might be empty)
            if len(straight_cards) >= 3:
                combos.append({
                    'combo_type': 'straight',
                    'rank_value': (end % 13),  # highest rank in straight (never 12)
                    'cards': straight_cards
                })
            else:
                # If failed to build, put back consumed (rare)
                for c in straight_cards:
                    r = c % 13
                    rank_to_cards.setdefault(r, []).insert(0, c)
                break

            # Continue loop to try detect more straights from remaining cards

        # Detect quads, triples, pairs
        for rank in list(sorted(rank_to_cards.keys())):
            cards = rank_to_cards.get(rank, [])
            if not cards:
                continue
            count = len(cards)
            if count >= 4:
                combos.append({'combo_type': 'quad', 'rank_value': rank, 'cards': cards[:4]})
                rank_to_cards[rank] = cards[4:]
            elif count == 3:
                combos.append({'combo_type': 'triple', 'rank_value': rank, 'cards': cards[:3]})
                rank_to_cards[rank] = cards[3:]
            elif count == 2:
                combos.append({'combo_type': 'pair', 'rank_value': rank, 'cards': cards[:2]})
                rank_to_cards[rank] = cards[2:]

        # Remaining singles
        for rank in list(sorted(rank_to_cards.keys())):
            cards = rank_to_cards.get(rank, [])
            for c in cards:
                combos.append({'combo_type': 'single', 'rank_value': rank, 'cards': [c]})
            rank_to_cards[rank] = []

        return combos
    
    @staticmethod
    def calculate_combo_strength(combo: Dict[str, Any]) -> float:
        """
        Calculate Sam-specific combo strength with ultra clear tiers
        
        Args:
            combo: Dictionary with combo_type, rank_value, cards
            
        Returns:
            Strength value between 0.0 and 1.0
        """
        combo_type = combo['combo_type']
        rank_value = combo.get('rank_value', 0)  # 0..12 where 12 == 2, 11 == A
        cards = combo.get('cards', [])

        is_two = (rank_value == 12)
        is_ace = (rank_value == 11)
        is_face = rank_value in (8, 9, 10)  # J, Q, K

        # Straights
        if combo_type == 'straight':
            length = len(cards)
            if length >= 10:
                return 1.0  # Sảnh rồng
            ranks = [c % 13 for c in cards]
            has_ace = any(r == 11 for r in ranks)
            if has_ace:
                return 1.0  # Ace-high straight
            
            if length >= 7:
                return 0.85 + (length - 7) * 0.02  # 7+ cards
            elif length == 6:
                return 0.6 + (rank_value / 11.0) * 0.05  # 6 cards
            elif length == 5:
                return 0.4 + (rank_value / 11.0) * 0.05  # 5 cards
            else:
                # 3-4 cards - INCREASED STRENGTH to compete with singles
                length_bonus = (length - 3) * 0.15  # Increased from 0.05
                rank_bonus = (rank_value / 11.0) * 0.05  # Increased from 0.02
                base_strength = 0.5  # Increased from 0.3
                return base_strength + length_bonus + rank_bonus

        # Singles
        if combo_type == 'single':
            if is_two:
                return 1.0
            if is_ace:
                return 0.3
            return 0.1 + (min(rank_value, 7) / 7.0) * 0.1

        # Pairs
        if combo_type == 'pair':
            if is_two:
                return 1.0
            if is_ace:
                return 0.8
            return 0.2 + (min(rank_value, 7) / 7.0) * 0.1

        # Triples
        if combo_type == 'triple':
            if is_two:
                return 1.0
            if is_ace:
                return 0.9
            if is_face:
                return 0.8
            if rank_value >= 4:  # >= 7
                return 0.5
            return 0.3 + (rank_value / 4.0) * 0.05

        # Quads
        if combo_type == 'quad' or combo_type == 'four_kind':
            if is_two:
                return 1.0
            if is_ace:
                return 0.98
            return 0.95 + (rank_value / 11.0) * 0.03

        return 0.1  # Fallback
