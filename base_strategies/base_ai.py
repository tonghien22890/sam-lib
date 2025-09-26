"""
Base AI - Base AI class that all AI inherit from
"""

from typing import List, Optional, Tuple
from game_engine.interfaces.ai_interface import AIInterface
from game_engine.core.game_entities import Move, GameState, PlayerAction
from game_engine.core.card_encoding import Card
from ..penalty_avoidance.penalty_checker import PenaltyChecker
from ..penalty_avoidance.penalty_types import PenaltyRisk, PenaltySeverity
from ..evaluators.move_evaluator import MoveEvaluator
from ..memory.card_memory import CardMemory


class BaseAI(AIInterface):
    """Base AI class that all AI inherit from"""
    
    def __init__(self, player_id: int, name: str):
        super().__init__(player_id, name)
        self.penalty_checker = PenaltyChecker()
        self.move_evaluator = MoveEvaluator()
        self.card_memory = CardMemory()
        self.game_type = None  # Will be set by game controller
        self.memory_enabled = True
    
    def choose_move(
        self, 
        hand: List[Card], 
        legal_moves: List[Move], 
        game_state: GameState,
        can_pass: bool = True
    ) -> Tuple[PlayerAction, Optional[List[Card]]]:
        """Base move selection with penalty avoidance"""
        
        # 1. Check penalty risks
        if self.game_type == "tlmn":
            penalty_risks = self.penalty_checker.check_tlmn_penalties(hand, game_state)
        else:  # sam
            penalty_risks = self.penalty_checker.check_sam_penalties(hand, game_state)
        
        # 2. Filter moves that avoid penalties
        safe_moves = self._filter_safe_moves(legal_moves, penalty_risks)
        
        # 3. If no safe moves, use all legal moves
        if not safe_moves:
            safe_moves = legal_moves
        
        # 4. Apply specific strategy
        return self._apply_strategy(safe_moves, hand, game_state, can_pass)
    
    def _filter_safe_moves(self, moves: List[Move], penalty_risks: List[PenaltyRisk]) -> List[Move]:
        """Filter moves that avoid penalties"""
        safe_moves = []
        
        for move in moves:
            if self._is_safe_move(move, penalty_risks):
                safe_moves.append(move)
        
        return safe_moves
    
    def _is_safe_move(self, move: Move, penalty_risks: List[PenaltyRisk]) -> bool:
        """Check if a move is safe (doesn't increase penalty risk)"""
        # This is a simplified implementation
        # In reality, this would analyze the move's impact on penalty risks
        
        # For now, prioritize moves that get rid of dangerous cards
        if hasattr(move, 'cards'):
            for card in move.cards:
                # Prioritize getting rid of 2♠
                if card.rank.value == 12 and card.suit.value == 3:  # 2♠
                    return True
                # Prioritize getting rid of other 2s
                if card.rank.value == 12:
                    return True
        
        return True  # Default to safe
    
    def _apply_strategy(self, moves: List[Move], hand: List[Card], game_state: GameState, can_pass: bool) -> Tuple[PlayerAction, Optional[List[Card]]]:
        """Apply specific AI strategy - to be overridden by subclasses"""
        # Use advanced move evaluation
        if moves:
            ranked_moves = self.move_evaluator.get_move_rankings(moves, hand, game_state, self.game_type)
            
            # Select best move
            if ranked_moves:
                best_move, best_score = ranked_moves[0]
                if hasattr(best_move, 'cards') and best_score > 0.1:  # Lower threshold
                    return PlayerAction.PLAY_CARDS, best_move.cards
        
        # If no good moves, try simple strategy
        if moves:
            # Simple strategy: play first move
            move = moves[0]
            if hasattr(move, 'cards') and move.cards:
                return PlayerAction.PLAY_CARDS, move.cards
        
        # If no moves or can't play, pass
        if can_pass:
            return PlayerAction.PASS, None
        else:
            # This shouldn't happen in a well-formed game
            return PlayerAction.PASS, None
    
    def update_memory(self, move: Move, game_state: GameState):
        """Update memory with a move (called by game controller)"""
        if self.memory_enabled:
            self.card_memory.update_with_move(self.player_id, move, game_state)
    
    def get_memory_insights(self) -> dict:
        """Get memory insights for debugging/analysis"""
        if not self.memory_enabled:
            return {"memory_disabled": True}
        
        return {
            "memory_enabled": True,
            "played_cards_count": len(self.card_memory.played_cards),
            "remaining_cards_count": len(self.card_memory.remaining_cards),
            "move_history_count": len(self.card_memory.move_history),
            "strategic_insights": self.card_memory.get_strategic_insights()
        }
    
    def get_ai_info(self) -> dict:
        """Get AI information"""
        return {
            "name": self.name,
            "player_id": self.player_id,
            "strategy": "base",
            "game_type": self.game_type
        }
    
    def set_game_type(self, game_type: str):
        """Set the game type for penalty checking"""
        self.game_type = game_type
