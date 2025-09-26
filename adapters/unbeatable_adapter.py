"""
Adapter for Unbeatable Sequence Model (Báo Sâm)
Integrates the new 3-phase ML pipeline with the game system
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

from ai_common.core.combo_analyzer import ComboAnalyzer
from ai_common.rules.sam_rule_engine import SamRuleEngine
from ai_common.probability.unbeatable_calculator import UnbeatableProbabilityCalculator
from ai_common.providers.sequence_order_provider import SequenceOrderProvider

logger = logging.getLogger(__name__)

class UnbeatableAdapter:
    """Adapter for Unbeatable Sequence Model (Báo Sâm decisions)
    
    Responsibilities:
      - Load the 3-phase Unbeatable Sequence Model
      - Provide should_declare_bao_sam(hand, player_count) interface
      - Handle model loading and fallback logic
    """
    
    def __init__(self, model_dir: Optional[str] = None) -> None:
        # Default model directory
        if model_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up two levels: adapters -> ai_common -> project root
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_dir = os.path.join(project_root, "model_build", "models")
        
        self.model_dir = model_dir
        self._generator = None
        self._is_loaded = False
        
        # Initialize core utilities
        self.combo_analyzer = ComboAnalyzer()
        self.rule_engine = SamRuleEngine()
        self.probability_calculator = UnbeatableProbabilityCalculator()
        self.sequence_order_provider = SequenceOrderProvider()
    
    def ensure_ready(self) -> bool:
        """Ensure the Unbeatable Sequence Model is loaded"""
        if self._is_loaded and self._generator is not None:
            return True
        
        try:
            # Add model_build and scripts/unbeatable to path for imports/unpickling
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up two levels: adapters -> ai_common -> project root
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_build_path = os.path.join(project_root, "model_build")
            unbeatable_scripts_path = os.path.join(model_build_path, "scripts", "unbeatable")
            
            if model_build_path not in sys.path:
                sys.path.insert(0, model_build_path)
            if unbeatable_scripts_path not in sys.path:
                sys.path.insert(0, unbeatable_scripts_path)
            
            # Import the Unbeatable Sequence Generator
            from model_build.scripts.unbeatable.unbeatable_sequence_model import UnbeatableSequenceGenerator
            
            # Initialize generator
            self._generator = UnbeatableSequenceGenerator()
            
            # Try to load pre-trained models
            if os.path.exists(self.model_dir):
                try:
                    self._generator.load_models(self.model_dir)
                    logger.info("UnbeatableAdapter: Loaded pre-trained models from %s", self.model_dir)
                except Exception as e:
                    logger.warning("UnbeatableAdapter: Failed to load pre-trained models: %s", e)
                    logger.info("UnbeatableAdapter: Using untrained models (will need training)")
            else:
                logger.warning("UnbeatableAdapter: Model directory not found: %s", self.model_dir)
                logger.info("UnbeatableAdapter: Using untrained models (will need training)")
            
            self._is_loaded = True
            return True
            
        except Exception as e:
            logger.error("UnbeatableAdapter: Failed to initialize: %s", e)
            return False
    
    def should_declare_bao_sam(self, hand: List[int], player_count: int = 4) -> Dict[str, Any]:
        """Make Báo Sâm declaration decision using Unbeatable Sequence Model
        
        Args:
            hand: List of card indices (0-51)
            player_count: Number of players in the game
            
        Returns:
            Dict with decision details:
            {
                'should_declare': bool,
                'unbeatable_probability': float,
                'user_threshold': float,
                'model_confidence': float,
                'reason': str,
                'unbeatable_sequence': List[Dict] or None,
                'sequence_stats': Dict or None
            }
        """
        if not self.ensure_ready():
            # Fallback: conservative decision
            return {
                'should_declare': False,
                'unbeatable_probability': 0.0,
                'user_threshold': 0.8,
                'model_confidence': 0.0,
                'reason': 'model_not_available',
                'unbeatable_sequence': None,
                'sequence_stats': None
            }
        
        try:
            # Use the Unbeatable Sequence Generator
            result = self._generator.generate_sequence(hand, player_count)
            
            # Ensure boolean type for compatibility
            result['should_declare'] = bool(result.get('should_declare_bao_sam', False))
            
            # Log detailed decision information
            logger.info(f"UnbeatableAdapter decision for hand {hand[:5]}...:")
            logger.info(f"  Should declare: {result['should_declare']}")
            logger.info(f"  Unbeatable probability: {result.get('unbeatable_probability', 0):.3f}")
            logger.info(f"  User threshold: {result.get('user_threshold', 0):.3f}")
            logger.info(f"  Model confidence: {result.get('model_confidence', 0):.3f}")
            logger.info(f"  Reason: {result.get('reason', 'unknown')}")
            
            return result
            
        except Exception as e:
            logger.error("UnbeatableAdapter: Error in should_declare_bao_sam: %s", e)
            return {
                'should_declare': False,
                'unbeatable_probability': 0.0,
                'user_threshold': 0.8,
                'model_confidence': 0.0,
                'reason': f'error_{str(e)}',
                'unbeatable_sequence': None,
                'sequence_stats': None
            }
    
    def get_ordered_sequence(self, hand: List[int], player_count: int = 4, 
                           strategy: str = "bao_sam_optimal") -> Dict[str, Any]:
        """
        Get ordered sequence for consistent gameplay
        
        Args:
            hand: List of card indices (0-51)
            player_count: Number of players
            strategy: Strategy type for ordering
            
        Returns:
            Dictionary with ordered sequence and metadata
        """
        return self.sequence_order_provider.get_sequence_with_strategy(hand, player_count, strategy)
    
    def validate_sequence_consistency(self, hand: List[int], player_count: int = 4) -> Dict[str, Any]:
        """
        Validate that sequence order is consistent with Báo Sâm decision
        
        Args:
            hand: List of card indices
            player_count: Number of players
            
        Returns:
            Validation results
        """
        return self.sequence_order_provider.validate_sequence_consistency(hand, player_count)
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of the loaded model"""
        if not self.ensure_ready():
            return {
                'loaded': False,
                'model_dir': self.model_dir,
                'status': 'failed_to_load'
            }
        
        # Check if models are trained
        model_files = [
            'validation_model.pkl',
            'pattern_model.pkl', 
            'threshold_model.pkl'
        ]
        
        trained_models = []
        for model_file in model_files:
            model_path = os.path.join(self.model_dir, model_file)
            if os.path.exists(model_path):
                trained_models.append(model_file)
        
        return {
            'loaded': True,
            'model_dir': self.model_dir,
            'trained_models': trained_models,
            'status': 'ready' if len(trained_models) == 3 else 'untrained',
            'generator_available': self._generator is not None,
            'core_utilities_available': {
                'combo_analyzer': self.combo_analyzer is not None,
                'rule_engine': self.rule_engine is not None,
                'probability_calculator': self.probability_calculator is not None,
                'sequence_order_provider': self.sequence_order_provider is not None
            }
        }
