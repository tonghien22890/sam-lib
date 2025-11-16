
#!/usr/bin/env python3
"""Unit tests for SequenceEvaluator priority-based sequence generation."""

import os
import sys
import unittest
from typing import Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from ai_common.core.sequence_evaluator import SequenceEvaluator


RANK_NAMES = ["3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "2"]
SUIT_NAMES = ["H", "D", "C", "S"]


def decode_card(card_id: int) -> str:
    return f"{RANK_NAMES[card_id % 13]}{SUIT_NAMES[card_id // 13]}"


def format_combo(combo: Dict[str, Any]) -> str:
    cards = ", ".join(decode_card(c) for c in combo["cards"])
    return f"{combo['type']}[{cards}]"


class SequenceEvaluatorTests(unittest.TestCase):
    """Validate core behaviors of the SequenceEvaluator."""

    def test_sequence_evaluator_hand_variants(self):
        evaluator = SequenceEvaluator(enforce_full_coverage=False)

        test_cases = {
            "Mixed triple + straight": [34, 21, 33, 8, 35, 36, 37, 39, 1, 28],
            "Four_kind heavy hand": [0, 13, 26, 39, 1, 14, 2, 15, 28, 3, 16],
            "Double sequence potential": [4, 17, 30, 5, 18, 31, 6, 19, 32, 40, 41],
            "Multiple twos scenario": [12, 25, 38, 11, 24, 37, 10, 23],
            "Junk singles heavy": [0, 14, 27, 3, 16, 29, 7, 20, 33, 46],
            "Short finish hand": [3, 16, 29, 8, 21, 34],  # straight + pair
            "Strong finish ordering": [11, 24, 37, 34, 21, 8, 9, 22],
        }

        for label, hand in test_cases.items():
            results = evaluator.evaluate_top_sequences(hand, k=3)

            print(f"\n{label} - Top 3 sequences:")
            for idx, seq in enumerate(results, start=1):
                combos_preview = [format_combo(combo) for combo in seq["sequence"]]
                print(f"  #{idx} avg={seq['avg_combo_strength']:.3f} combos={combos_preview}")

            self.assertEqual(len(results), 3)
            avg_strengths = [round(seq["avg_combo_strength"], 3) for seq in results]
            self.assertEqual(avg_strengths, sorted(avg_strengths, reverse=True))
            # Extra check for multi-2 case: ensure first combo is strong
            if label == "Multiple twos scenario":
                first_combo = results[0]["sequence"][0]
                self.assertIn(first_combo["type"], {"straight", "four_kind", "triple", "pair"})
            
            if label == "Junk singles heavy":
                single_count = sum(
                    1 for seq in results for combo in seq["sequence"] if combo["type"] == "single"
                )
                self.assertGreaterEqual(single_count, 4)
            
            if label == "Strong finish ordering":
                seq = results[0]["sequence"]
                strengths = [combo["strength"] for combo in seq]
                self.assertAlmostEqual(strengths[-1], min(strengths))
                self.assertAlmostEqual(strengths[-2], max(strengths[:-1]))



if __name__ == "__main__":
    unittest.main()

