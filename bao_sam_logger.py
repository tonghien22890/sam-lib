"""
Báo Sâm Logger for Web Backend

This module provides logging functionality specifically for Báo Sâm declarations
according to the schema defined in SAM_DECLARATION.mdc.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

class BaoSamLogger:
    """Logger for Báo Sâm declaration data"""
    
    def __init__(self, file_path: str = "bao_sam_data.jsonl"):
        self.file_path = file_path
    
    def log_bao_sam_declaration(self, game_id: str, player_id: int, 
                               hand: List[int], sammove_sequence: List[Dict[str, Any]], 
                               result: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a Báo Sâm declaration record
        
        Args:
            game_id: Unique game identifier
            player_id: Player who declared Báo Sâm
            hand: Original hand cards (IDs 0-51)
            sammove_sequence: Sequence of combos played during Báo Sâm
            result: "success" or "fail"
            meta: Additional metadata
        """
        if meta is None:
            meta = {}
        
        # Calculate meta information
        num_combos = len(sammove_sequence)
        num_cards = sum(len(combo.get('cards', [])) for combo in sammove_sequence)
        
        # Validate data
        if num_cards != len(hand):
            print(f"⚠️  Warning: Báo Sâm sequence uses {num_cards} cards but hand has {len(hand)}")
        
        record = {
            "game_id": game_id,
            "player_id": player_id,
            "hand": hand,
            "sammove_sequence": sammove_sequence,
            "result": result,
            "meta": {
                "num_combos": num_combos,
                "num_cards": num_cards,
                **meta  # Merge additional meta data
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            print(f"✅ Logged Báo Sâm declaration: {result} by player {player_id}")
        except Exception as e:
            print(f"❌ Failed to log Báo Sâm declaration: {e}")
    
    def get_bao_sam_stats(self) -> Dict[str, Any]:
        """Get statistics about logged Báo Sâm declarations"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                records = [json.loads(line.strip()) for line in f if line.strip()]
            
            total_declarations = len(records)
            successful_declarations = sum(1 for r in records if r['result'] == 'success')
            failed_declarations = total_declarations - successful_declarations
            
            avg_combos = sum(r['meta']['num_combos'] for r in records) / max(total_declarations, 1)
            avg_cards = sum(r['meta']['num_cards'] for r in records) / max(total_declarations, 1)
            
            return {
                "total_declarations": total_declarations,
                "successful": successful_declarations,
                "failed": failed_declarations,
                "success_rate": successful_declarations / max(total_declarations, 1),
                "avg_combos_per_declaration": avg_combos,
                "avg_cards_per_declaration": avg_cards
            }
        except FileNotFoundError:
            return {"error": "No Báo Sâm data file found"}
        except Exception as e:
            return {"error": f"Failed to read stats: {e}"}
