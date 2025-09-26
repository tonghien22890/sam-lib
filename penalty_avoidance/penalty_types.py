"""
Penalty Types - Enumeration of penalty risks
"""

from enum import Enum


class PenaltyRisk(Enum):
    """Types of penalty risks in Vietnamese card games"""
    
    # TLMN Penalties
    THOI_2_SPADES = "thoi_2_spades"           # Thối 2♠ (-26 bets)
    THOI_FOUR_KIND = "thoi_four_kind"         # Thối tứ quý (-26 bets)
    THOI_THREE_PAIRS = "thoi_three_pairs"     # Thối 3 đôi thông (-26 bets)
    THOI_FOUR_PAIRS = "thoi_four_pairs"       # Thối 4 đôi thông (-26 bets)
    
    # Sam Penalties
    THOI_2_SPADES_SAM = "thoi_2_spades_sam"   # Thối 2♠ in Sam (-26 bets)
    THOI_FOUR_KIND_SAM = "thoi_four_kind_sam" # Thối tứ quý in Sam (-26 bets)
    CONG = "cong"                             # Cóng - can't play any card (-26 bets)
    PHAT_SAM = "phat_sam"                     # Phạt Sâm - declared but didn't win (-26 bets)
    
    # General Risks
    HIGH_CARD_RISK = "high_card_risk"         # Risk of being left with high cards
    COMBO_BREAK_RISK = "combo_break_risk"     # Risk of breaking good combinations


class PenaltySeverity(Enum):
    """Severity levels of penalties"""
    CRITICAL = 3    # -26 bets (must avoid at all costs)
    HIGH = 2        # -13 bets
    MEDIUM = 1      # -6 bets
    LOW = 0         # -1 bet
