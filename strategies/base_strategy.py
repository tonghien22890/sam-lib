"""
Base Strategy

Base class for all AI strategies, providing common
functionality and ensuring consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyConfig:
    """Strategy configuration"""
    name: str
    game_type: str
    aggressiveness: float = 0.5  # 0.0 = conservative, 1.0 = aggressive
    risk_tolerance: float = 0.5  # 0.0 = risk-averse, 1.0 = risk-taking
    metadata: Dict[str, Any] = None


class BaseStrategy(ABC):
    """
    Base class for all AI strategies.
    
    Provides common functionality including:
    - Move evaluation and selection
    - Risk assessment
    - Game state analysis
    - Performance tracking
    """
    
    def __init__(self, config: StrategyConfig):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self._performance_stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'average_decision_time': 0.0,
            'last_decision_time': 0.0
        }
    
    @abstractmethod
    def evaluate_move(self, move: Dict[str, Any], game_state: Dict[str, Any]) -> float:
        """
        Evaluate a move and return a score
        
        Args:
            move: Move to evaluate
            game_state: Current game state
            
        Returns:
            float: Move score (higher is better)
        """
        pass
    
    @abstractmethod
    def select_best_move(self, legal_moves: List[Dict[str, Any]], 
                        game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the best move from legal moves
        
        Args:
            legal_moves: Available legal moves
            game_state: Current game state
            
        Returns:
            Dict containing the selected move
        """
        pass
    
    @abstractmethod
    def should_declare_special(self, game_state: Dict[str, Any]) -> bool:
        """
        Determine if should declare special action (e.g., Báo Sâm, Tới trắng)
        
        Args:
            game_state: Current game state
            
        Returns:
            bool: True if should declare special action
        """
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and capabilities
        
        Returns:
            Dict containing strategy metadata
        """
        return {
            'name': self.config.name,
            'game_type': self.config.game_type,
            'aggressiveness': self.config.aggressiveness,
            'risk_tolerance': self.config.risk_tolerance,
            'performance_stats': self._performance_stats.copy()
        }
    
    def reset_performance_stats(self) -> None:
        """Reset performance statistics"""
        self._performance_stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'average_decision_time': 0.0,
            'last_decision_time': 0.0
        }
    
    def _update_performance_stats(self, success: bool, decision_time: float) -> None:
        """
        Update performance statistics
        
        Args:
            success: Whether decision was successful
            decision_time: Time taken for decision
        """
        stats = self._performance_stats
        stats['total_decisions'] += 1
        stats['last_decision_time'] = decision_time
        
        if success:
            stats['successful_decisions'] += 1
        else:
            stats['failed_decisions'] += 1
        
        # Update average decision time
        total_time = stats['average_decision_time'] * (stats['total_decisions'] - 1)
        stats['average_decision_time'] = (total_time + decision_time) / stats['total_decisions']
