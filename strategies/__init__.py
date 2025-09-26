"""
AI Strategies

This module provides AI strategies for different game types,
ensuring consistent behavior across different AI implementations.
"""

from .base_strategy import BaseStrategy
from .tlmn_strategy import TLMNStrategy
from .sam_strategy import SamStrategy

__all__ = [
    'BaseStrategy',
    'TLMNStrategy', 
    'SamStrategy'
]
