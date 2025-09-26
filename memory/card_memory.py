"""
Card Memory System - Advanced card counting and game memory
"""

from typing import List, Dict, Set, Optional
from game_engine.core.card_encoding import Card, Rank, Suit
from game_engine.core.game_entities import GameState, Move


class CardMemory:
    """Advanced card counting and memory system"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset memory for new game"""
        self.played_cards: Set[Card] = set()
        self.remaining_cards: Set[Card] = set()
        self.player_hands: Dict[int, Set[Card]] = {}
        self.move_history: List[Dict] = []
        
        # Initialize with all 52 cards
        for card_id in range(52):
            card = Card.from_id(card_id)
            self.remaining_cards.add(card)
    
    def update_with_move(self, player_id: int, move: Move, game_state: GameState):
        """Update memory with a new move"""
        if hasattr(move, 'cards') and move.cards:
            for card in move.cards:
                self.played_cards.add(card)
                self.remaining_cards.discard(card)
        
        # Update move history
        move_record = {
            "player_id": player_id,
            "move": move,
            "turn": game_state.turn_id,
            "round": game_state.round_id
        }
        self.move_history.append(move_record)
    
    def get_remaining_cards(self) -> Set[Card]:
        """Get all remaining unplayed cards"""
        return self.remaining_cards.copy()
    
    def get_played_cards(self) -> Set[Card]:
        """Get all played cards"""
        return self.played_cards.copy()
    
    def get_remaining_count_by_rank(self, rank: Rank) -> int:
        """Get count of remaining cards of a specific rank"""
        return sum(1 for card in self.remaining_cards if card.rank == rank)
    
    def get_remaining_count_by_suit(self, suit: Suit) -> int:
        """Get count of remaining cards of a specific suit"""
        return sum(1 for card in self.remaining_cards if card.suit == suit)
    
    def get_played_count_by_rank(self, rank: Rank) -> int:
        """Get count of played cards of a specific rank"""
        return sum(1 for card in self.played_cards if card.rank == rank)
    
    def get_played_count_by_suit(self, suit: Suit) -> int:
        """Get count of played cards of a specific suit"""
        return sum(1 for card in self.played_cards if card.suit == suit)
    
    def is_card_played(self, card: Card) -> bool:
        """Check if a specific card has been played"""
        return card in self.played_cards
    
    def is_card_remaining(self, card: Card) -> bool:
        """Check if a specific card is still remaining"""
        return card in self.remaining_cards
    
    def get_probability_of_rank(self, rank: Rank) -> float:
        """Get probability that a specific rank is still available"""
        remaining = self.get_remaining_count_by_rank(rank)
        total_remaining = len(self.remaining_cards)
        
        if total_remaining == 0:
            return 0.0
        
        return remaining / total_remaining
    
    def get_probability_of_suit(self, suit: Suit) -> float:
        """Get probability that a specific suit is still available"""
        remaining = self.get_remaining_count_by_suit(suit)
        total_remaining = len(self.remaining_cards)
        
        if total_remaining == 0:
            return 0.0
        
        return remaining / total_remaining
    
    def get_opponent_hand_estimate(self, player_id: int, known_hand: List[Card]) -> Dict[str, float]:
        """Estimate opponent's hand based on memory and known cards"""
        estimate = {
            "high_cards_probability": 0.0,
            "pairs_probability": 0.0,
            "combos_probability": 0.0,
            "dangerous_cards_probability": 0.0
        }
        
        # Calculate probabilities based on remaining cards
        remaining = self.get_remaining_cards()
        
        # High cards (J, Q, K, A, 2)
        high_cards_remaining = sum(1 for card in remaining if card.rank.value >= 8)
        estimate["high_cards_probability"] = high_cards_remaining / len(remaining) if remaining else 0
        
        # Dangerous cards (2♠, other 2s)
        dangerous_cards_remaining = sum(1 for card in remaining if card.rank == Rank.TWO)
        estimate["dangerous_cards_probability"] = dangerous_cards_remaining / len(remaining) if remaining else 0
        
        return estimate
    
    def get_move_statistics(self) -> Dict[str, any]:
        """Get statistics about moves played"""
        if not self.move_history:
            return {}
        
        stats = {
            "total_moves": len(self.move_history),
            "moves_by_player": {},
            "combo_types": {},
            "cards_played_per_turn": []
        }
        
        # Count moves by player
        for move_record in self.move_history:
            player_id = move_record["player_id"]
            stats["moves_by_player"][player_id] = stats["moves_by_player"].get(player_id, 0) + 1
            
            # Count combo types
            if hasattr(move_record["move"], 'combo_type'):
                combo_type = move_record["move"].combo_type.value
                stats["combo_types"][combo_type] = stats["combo_types"].get(combo_type, 0) + 1
        
        return stats
    
    def get_strategic_insights(self) -> Dict[str, any]:
        """Get strategic insights based on memory"""
        insights = {
            "critical_cards_remaining": [],
            "safe_plays": [],
            "risky_plays": [],
            "opponent_patterns": {}
        }
        
        remaining = self.get_remaining_cards()
        
        # Critical cards (2♠, other 2s, high cards)
        for card in remaining:
            if card.rank == Rank.TWO and card.suit == Suit.SPADES:
                insights["critical_cards_remaining"].append("2♠")
            elif card.rank == Rank.TWO:
                insights["critical_cards_remaining"].append(f"2{card.suit.name[0]}")
            elif card.rank.value >= 10:
                insights["critical_cards_remaining"].append(str(card))
        
        # Analyze opponent patterns
        for move_record in self.move_history:
            player_id = move_record["player_id"]
            if player_id not in insights["opponent_patterns"]:
                insights["opponent_patterns"][player_id] = {
                    "aggressive_moves": 0,
                    "conservative_moves": 0,
                    "combo_preferences": {}
                }
            
            # Analyze move patterns (simplified)
            if hasattr(move_record["move"], 'cards') and move_record["move"].cards:
                avg_value = sum(card.rank.value for card in move_record["move"].cards) / len(move_record["move"].cards)
                if avg_value >= 6:  # High cards
                    insights["opponent_patterns"][player_id]["aggressive_moves"] += 1
                else:
                    insights["opponent_patterns"][player_id]["conservative_moves"] += 1
        
        return insights
