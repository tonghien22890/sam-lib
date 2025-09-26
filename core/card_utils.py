"""
Card utility functions for AI-Sam
"""

from typing import List, Dict, Any


class CardUtils:
    """Utility functions for card operations"""
    
    @staticmethod
    def card_to_string(card_id: int) -> str:
        """
        Convert card ID (0-51) to human readable string
        
        Args:
            card_id: Card index (0-51)
            
        Returns:
            String representation like "3♠", "A♥", "2♣"
        """
        suit_symbols = ['♠', '♥', '♦', '♣']
        rank_symbols = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
        
        suit = card_id // 13
        rank = card_id % 13
        
        return f"{rank_symbols[rank]}{suit_symbols[suit]}"
    
    @staticmethod
    def hand_to_string(hand: List[int]) -> str:
        """
        Convert hand to human readable string
        
        Args:
            hand: List of card IDs
            
        Returns:
            String representation like "3♠ 4♠ 5♠ ..."
        """
        return " ".join(CardUtils.card_to_string(card_id) for card_id in sorted(hand))
    
    @staticmethod
    def combo_to_string(combo: Dict[str, Any]) -> str:
        """
        Convert combo to human readable string
        
        Args:
            combo: Combo dictionary with combo_type, rank_value, cards
            
        Returns:
            String representation like "straight: 3♠-7♠"
        """
        combo_type = combo['combo_type']
        cards = combo.get('cards', [])
        card_strings = [CardUtils.card_to_string(card_id) for card_id in sorted(cards)]
        
        if combo_type == 'straight' and len(cards) > 1:
            return f"{combo_type}: {card_strings[0]}-{card_strings[-1]}"
        else:
            return f"{combo_type}: {' '.join(card_strings)}"
    
    @staticmethod
    def combos_to_string(combos: List[Dict[str, Any]]) -> str:
        """
        Convert list of combos to human readable string
        
        Args:
            combos: List of combo dictionaries
            
        Returns:
            String representation of all combos
        """
        return " | ".join(CardUtils.combo_to_string(combo) for combo in combos)
