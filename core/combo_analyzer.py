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
        
        Strategy (CORRECT for Sâm game):
        1) Detect FOUR OF A KIND first (strongest combo)
        2) Then detect STRAIGHTS from remaining cards
        3) Then detect THREE OF A KIND
        4) Then detect PAIRS
        5) Remaining as SINGLES
        
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

        # STEP 1: Detect FOUR OF A KIND first (strongest combo in Sâm)
        for rank in list(sorted(rank_to_cards.keys())):
            cards = rank_to_cards.get(rank, [])
            if len(cards) >= 4:
                combos.append({'combo_type': 'four_kind', 'rank_value': rank, 'cards': cards[:4]})
                rank_to_cards[rank] = cards[4:]

        # STEP 2: Detect STRAIGHTS from remaining cards
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

            # Only create straights of length >= 3
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

        # STEP 3: Detect THREE OF A KIND from remaining cards
        for rank in list(sorted(rank_to_cards.keys())):
            cards = rank_to_cards.get(rank, [])
            if len(cards) >= 3:
                combos.append({'combo_type': 'triple', 'rank_value': rank, 'cards': cards[:3]})
                rank_to_cards[rank] = cards[3:]

        # STEP 4: Detect PAIRS from remaining cards
        for rank in list(sorted(rank_to_cards.keys())):
            cards = rank_to_cards.get(rank, [])
            if len(cards) >= 2:
                combos.append({'combo_type': 'pair', 'rank_value': rank, 'cards': cards[:2]})
                rank_to_cards[rank] = cards[2:]

        # STEP 5: Remaining SINGLES
        for rank in list(sorted(rank_to_cards.keys())):
            cards = rank_to_cards.get(rank, [])
            for c in cards:
                combos.append({'combo_type': 'single', 'rank_value': rank, 'cards': [c]})
            rank_to_cards[rank] = []

        return combos
    
    @staticmethod
    def calculate_unbeatable_strength(combo: Dict[str, Any]) -> float:
        """
        Calculate Unbeatable/Báo Sâm specific combo strength
        
        Logic: Báo Sâm = đánh mạnh trước, yếu sau
        - High strength = giữ lại đánh cuối (weak combos)
        - Low strength = đánh trước (strong combos)
        
        Strength rules:
        - Straight đến A: 1.0 (không thể chặn)
        - Straight >=7: 0.6-0.9+ (dây dài mạnh)
        - Straight 6 có mặt người: 0.65
        - Straight khác: 0.2-0.49 (dây ngắn yếu)
        - Triple 2: 1.0 (tuyệt đối)
        - Triple A: 0.6 (mạnh)
        - Triple J/Q/K: 0.55 (trung bình)
        - Triple 8-10 (rank>=5): 0.5 (trung bình)
        - Triple khác: 0.1 (yếu)
        - Single 2: 0.9 (giữ lại cuối)
        - Single/Pair khác: 0.1 (đánh sớm)
        - Pair 2: 0.95 (rất mạnh)
        
        Args:
            combo: Dictionary with combo_type, rank_value, cards
            
        Returns:
            Strength value between 0.0 and 1.0 (higher = keep longer)
        """
        combo_type = combo['combo_type']
        rank_value = combo.get('rank_value', 0)  # 0..12 where 12 == 2, 11 == A
        cards = combo.get('cards', [])

        is_two = (rank_value == 12)
        is_ace = (rank_value == 11)
        is_face = rank_value in (8, 9, 10)  # J, Q, K

        # Straights - adjusted for Báo Sâm strategy
        if combo_type == 'straight':
            length = len(cards)
            
            # Dây đến A (rank 11) = dây cao nhất, không thể chặn
            if is_ace:
                return 1.0
            
            # Dây dài >=7: strength > 0.6
            if length >= 7:
                # Base strength 0.6 + length bonus
                base_strength = 0.65 + (length - 7) * 0.05  # 0.6 to 0.8+ for 7-15 cards
                # Face bonus for long straights
                if is_face:
                    return base_strength + 0.1  # 0.7 to 0.9+
                return base_strength  # 0.6 to 0.8+
            
            # Dây 6 có mặt người: strength > 0.6
            elif length == 6 and is_face:
                return 0.65  # Slightly above 0.6
            
            # Dây khác: strength < 0.5
            else:
                # Base strength < 0.5 for short straights
                base_strength = 0.2 + (length - 3) * 0.08  # 0.2 to 0.44 for 3-6 cards
                # Small face bonus
                if is_face:
                    return base_strength + 0.05  # Still < 0.5
                return base_strength

        # Singles - đánh sớm (low strength = play early)
        if combo_type == 'single':
            if is_two:
                return 0.9  # Single 2 giữ lại cuối (absolute power)
            if is_ace:
                return 0.1  # Single A đánh sớm
            return 0.1  # Single khác đánh sớm

        # Pairs - đánh sớm (low strength = play early)
        if combo_type == 'pair':
            if is_two:
                return 0.95  # Đôi 2 rất mạnh (near absolute power)
            return 0.1  # Đôi khác đánh sớm

        # Triples - phân tầng theo rank
        if combo_type == 'triple':
            if is_two:
                return 1.0  # Ba 2 tuyệt đối mạnh
            if is_ace:
                return 0.6  # Ba A mạnh
            if is_face:
                return 0.55  # Ba J/Q/K trung bình mạnh
            if rank_value >= 5:
                return 0.5  # Ba 8/9/10 (rank>=5) trung bình
            return 0.1  # Ba 3-7 yếu

        # Four of a kind - tuyệt đối mạnh
        if combo_type == 'four_kind':
            if is_two:
                return 1.0  # Tứ 2 tuyệt đối
            return 0.9  # Tứ khác rất mạnh

        # Pass
        if combo_type == 'pass':
            return 0.0

        return 0.0

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
        base_rank_strength = 0.1 + (min(rank_value, 7) / 7.0) * 0.1

        # Straights
        if combo_type == 'straight':
            length = len(cards)
            if length >= 10:
                return 1.0  # Sảnh rồng
            ranks = [c % 13 for c in cards]
            has_ace = any(r == 11 for r in ranks)
            if is_ace:
                return 1.0  # Ace-high straight
            
            # Rank is primary factor, length is bonus
            # High rank = keep for later, low rank + long length = play early
            
            # Base strength from rank (primary factor)
            rank_strength = 0.1 + (rank_value / 11.0) * 0.6  # 0.1 to 0.7
            
            # Length bonus (secondary factor)
            if length >= 7:
                length_bonus = 0.1 + (length - 7) * 0.02  # 0.1 to 0.26 for 7-15 cards
            elif length == 6:
                length_bonus = 0.08  # 6 cards
            elif length == 5:
                length_bonus = 0.06  # 5 cards
            else:
                # 3-4 cards - small length bonus
                length_bonus = (length - 3) * 0.03  # 0.0 to 0.03
            
            return rank_strength + length_bonus

        # Singles
        if combo_type == 'single':
            if is_two:
                return 1.0
            if is_ace:
                return 0.3
            return base_rank_strength

        # Pairs
        if combo_type == 'pair':
            if is_two:
                return 1.0
            if is_ace:
                return 0.8
            if rank_value > 4:
                return 0.3 + base_rank_strength
            return 0.15 + base_rank_strength

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
            return 0.25 + (rank_value / 4.0) * 0.05

        # Quads
        if combo_type == 'four_kind':
            if is_two:
                return 1.0
            if is_ace:
                return 0.98
            return 0.95 + (rank_value / 11.0) * 0.03

        return 0.1  # Fallback
