"""
JSONLines Logger for training data.

Purpose: centralize all logging utilities under ai_common for AI training.

Dataset schema (baseline, extensible):
{
  "game_id": str,
  "round_id": int,
  "turn_id": int,
  "player_id": int,

  "hand": [int],   // card IDs (0-51)

  "last_move": {
    "player_id": int,
    "cards": [int],
    "combo_type": str,
    "rank_value": int
  } | null,

  "players_left": [int],   // active player IDs
  "cards_left": [int],     // number of cards left per player (parallel to players_left)
  "hand_count": int,       // number of cards in current player's hand

  "action": {
    "stage1": {
      "type": "combo_type" | "pass",   // high-level action
      "value": str | "pass"            // e.g. "single", "pair", "straight"
    },
    "stage2": {
      "type": "play_cards" | "pass",
      "cards": [int],
      "combo_type": str | null,
      "rank_value": int | null
    }
  },

  "meta": {
    "legal_stage1": [str],   // valid combo types: ["single","pair","straight","pass",...]
    "legal_stage2": [
      { "type": str, "cards": [int], "combo_type": str, "rank_value": int }
    ]
  },

  // game-specific block (optional): "sam_state" | "tlmn_state" | ...
  // optional: "timestamp"
}

Notes:
- Keep keys stable for training. New fields should be additive.
- Use card IDs (0-51) consistently.
- Split action/meta into stage1 + stage2 to support two-step training.
- `cards_left`: Should be card counts per player [9, 8, 3, 3], not card IDs.
- `hand_count`: Automatically calculated from `hand` length if not provided.
- For model training, use `scripts/convert_training_data.py` to ensure proper format.
"""


from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, List

# Template describing required top-level keys and their types at a high level
DATASET_REQUIRED_KEYS: List[str] = [
    "game_id",
    "round_id",
    "turn_id",
    "player_id",
    "hand",
    "last_move",
    "players_left",
    "cards_left",
    "hand_count",
    "action",
    "meta",
]


class JSONLLogger:
    """Append-only JSONLines logger.

    Parameters:
        file_path: Path to the .jsonl file
        include_timestamp: If True, add an ISO timestamp to each record
    """

    def __init__(self, file_path: str, include_timestamp: bool = True) -> None:
        self.file_path = file_path
        self.include_timestamp = include_timestamp
        # Ensure parent directory exists if provided
        parent = os.path.dirname(os.path.abspath(file_path))
        if parent and not os.path.exists(parent):
            # Do not create new directories if they don't exist to respect repo constraints
            # Fallback to project root if directory is missing
            if parent != os.path.abspath(os.curdir):
                # Redirect to project root file
                base_name = os.path.basename(file_path)
                self.file_path = os.path.join(os.path.abspath(os.curdir), base_name)

    def write_record(self, record: Dict[str, Any]) -> None:
        """Write a single record as a JSON line."""
        if self.include_timestamp:
            record.setdefault("timestamp", datetime.utcnow().isoformat())
        with open(self.file_path, "a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

    def write_action(self, game_record: Dict[str, Any], action_record: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> None:
        """Merge game and action records and write.

        The game_record should match BaseGame.get_game_record() shape.
        action_record may be legacy flat shape or the new two-stage schema.
        """
        merged: Dict[str, Any] = {**game_record}
        merged["action"] = normalize_action_record(action_record)
        # Normalize general-play fields for model compatibility
        _ensure_pass_in_legal_moves(merged)
        _fill_stage2_combo_fields_from_legal(merged)
        _normalize_cards_left_counts(merged)
        if extra:
            merged.update(extra)
        for key in DATASET_REQUIRED_KEYS:
            if key not in merged:
                if key in ("hand", "players_left", "cards_left"):
                    merged[key] = []
                elif key == "hand_count":
                    # Calculate hand_count from hand length
                    merged[key] = len(merged.get("hand", []))
                elif key == "last_move":
                    merged[key] = None
                elif key == "action":
                    merged[key] = {
                        "stage1": {"type": "pass", "value": "pass"},
                        "stage2": {"type": "pass", "cards": [], "combo_type": None, "rank_value": None},
                    }
                elif key == "meta":
                    merged[key] = {"legal_stage1": [], "legal_stage2": []}
                else:
                    merged[key] = 0 if key.endswith("_id") or key.endswith("id") else None
        self.write_record(merged)

    def write_bao_sam(self, sammove_sequence: list, result: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Write a Bao Sâm training record.

        Required:
          - sammove_sequence: list of {cards:[int], combo_type:str, rank_value:int}
          - result: "success" | "fail"
        """
        record: Dict[str, Any] = {
            "sammove_sequence": sammove_sequence or [],
            "result": result,
        }
        if extra:
            record.update(extra)
        self.write_record(record)

def build_action_record_from_move(move: Dict[str, Any]) -> Dict[str, Any]:
    """Build a two-stage action record from a game-specific move dict/object.

    Expected move fields when available: type, cards(list[int]), combo_type(str), rank_value(int).
    Missing fields are defaulted to pass/empty.
    """
    move_type = move.get("type", "pass")
    combo_type = move.get("combo_type")
    rank_value = move.get("rank_value")
    cards = move.get("cards", [])

    if move_type == "play_cards" and combo_type:
        stage1 = {"type": "combo_type", "value": combo_type}
    else:
        stage1 = {"type": "pass", "value": "pass"}

    stage2: Dict[str, Any] = {
        "type": move_type if move_type in ("play_cards", "pass") else "pass",
        "cards": cards,
        "combo_type": combo_type if move_type == "play_cards" else None,
        "rank_value": rank_value if move_type == "play_cards" else None,
    }

    return {"stage1": stage1, "stage2": stage2}


def normalize_action_record(action_record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize incoming action into the two-stage schema.

    Accepts either the new two-stage structure or legacy flat structure.
    """
    if not isinstance(action_record, dict):
        return {"stage1": {"type": "pass", "value": "pass"}, "stage2": {"type": "pass", "cards": [], "combo_type": None, "rank_value": None}}
    if "stage1" in action_record and "stage2" in action_record:
        stage1 = action_record.get("stage1", {})
        stage2 = action_record.get("stage2", {})
        return {
            "stage1": {"type": stage1.get("type", "pass"), "value": stage1.get("value", "pass")},
            "stage2": {
                "type": stage2.get("type", "pass"),
                "cards": stage2.get("cards", []),
                "combo_type": stage2.get("combo_type", None),
                "rank_value": stage2.get("rank_value", None),
            },
        }
    return build_action_record_from_move(action_record)


# ---------------------------
# Normalization helpers
# ---------------------------

def _ensure_pass_in_legal_moves(rec: Dict[str, Any]) -> None:
    meta = rec.get("meta", {})
    legal = meta.get("legal_moves") or meta.get("legal_stage2")
    if not isinstance(legal, list):
        return
    has_pass = any((m.get("type") == "pass") for m in legal if isinstance(m, dict))
    if not has_pass:
        legal.append({"type": "pass", "cards": [], "combo_type": None, "rank_value": None})
        meta["legal_moves"] = legal
        rec["meta"] = meta

def _fill_stage2_combo_fields_from_legal(rec: Dict[str, Any]) -> None:
    """If action.stage2 is play_cards but missing combo_type/rank_value, infer from legal_moves by matching cards."""
    action = rec.get("action", {})
    stage2 = action.get("stage2", {})
    if stage2.get("type") != "play_cards":
        return
    if stage2.get("combo_type") is not None and stage2.get("rank_value") is not None:
        return
    cards = stage2.get("cards", [])
    meta = rec.get("meta", {})
    legal = meta.get("legal_moves") or meta.get("legal_stage2") or []
    for m in legal:
        if not isinstance(m, dict):
            continue
        if m.get("type") == "play_cards" and m.get("cards", []) == cards:
            stage2["combo_type"] = m.get("combo_type")
            stage2["rank_value"] = m.get("rank_value")
            action["stage2"] = stage2
            rec["action"] = action
            break

def _normalize_cards_left_counts(rec: Dict[str, Any]) -> None:
    """Ensure cards_left is a list of counts per player (e.g., [9,8,3,3]).

    Heuristic: if cards_left looks like card IDs (length > 10 or values > 13), clear it and let caller
    fill correctly or leave empty. If it's already small (<=4) and values are small, keep as-is.
    """
    cards_left = rec.get("cards_left")
    if not isinstance(cards_left, list):
        return
    if len(cards_left) <= 4 and all(isinstance(x, int) and 0 <= x <= 13 for x in cards_left):
        return  # looks like counts already
    # Otherwise, set to empty to avoid poisoning training; caller can provide proper counts
    rec["cards_left"] = []


