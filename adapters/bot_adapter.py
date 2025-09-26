from __future__ import annotations

from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)


class GeneralAdapter:
    """Adapter for general gameplay per-candidate model.

    Responsibilities:
      - Ensure model is loaded (lazy)
      - Provide predict(game_record, legal_moves) → best move
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "model_build",
            "models",
            "optimized_general_model_v3.pkl",
        )
        self._model = None
        self._has_candidate = False

    def ensure_ready(self) -> bool:
        if self._model is not None:
            return True
        try:
            from model_build.scripts.general.optimized_general_model_v3 import OptimizedGeneralModelV3  # type: ignore
        except Exception as e:
            logger.warning("GeneralAdapter deps missing: %s", e)
            return False
        if not os.path.exists(self.model_path):
            logger.warning("GeneralAdapter model not found at %s", self.model_path)
            return False
        try:
            model = OptimizedGeneralModelV3()
            model.load(self.model_path)
            # Backward-compat: accept older two-stage models
            if getattr(model, "candidate_model", None) is not None:
                self._has_candidate = True
            else:
                # Try fallback if classic stage1_model exists
                if getattr(model, "stage1_model", None) is None:
                    logger.warning("GeneralAdapter: no candidate model and no stage1_model in file")
                    return False
                logger.info("GeneralAdapter: using fallback two-stage model (no candidate model)")
            self._model = model
            logger.info("GeneralAdapter loaded model from %s", self.model_path)
            return True
        except Exception as e:
            logger.warning("GeneralAdapter failed to load: %s", e)
            return False

    def predict(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.ensure_ready():
            print("🤖 [GeneralAdapter] Model not ready, using fallback")
            # Fallback: pass or first move
            for m in legal_moves:
                if m.get("type") == "play_cards" and m.get("cards"):
                    return {"type": "play_cards", "cards": m.get("cards")}
            return {"type": "pass", "cards": []}

        model = self._model

        # Path A: candidate model available (preferred)
        if self._has_candidate and getattr(model, "candidate_model", None) is not None:
            print("🤖 [GeneralAdapter] Using per-candidate model (Path A)")
            record = {
                "hand": game_record.get("hand", []),
                "cards_left": game_record.get("cards_left", []),
                "meta": {"legal_moves": legal_moves},
            }
            
            # Log model info
            print(f"🤖 [GeneralAdapter] Model training data size: {getattr(model, 'training_data_size', 'unknown')}")
            try:
                info = model.get_hybrid_info()
                print(f"🤖 [GeneralAdapter] Hybrid info: size={info.get('training_data_size')} approach={info.get('approach')} threshold={info.get('threshold')}")
            except Exception:
                print(f"🤖 [GeneralAdapter] Using rank approach: {getattr(model, 'use_rank_category', 'unknown')}")
            
            import numpy as np  # local import to limit hard deps
            feats = [model.extract_candidate_features(record, m) for m in legal_moves]
            if not feats:
                print("🤖 [GeneralAdapter] No features extracted, passing")
                return {"type": "pass", "cards": []}
            
            # Log feature dimensions
            print(f"🤖 [GeneralAdapter] Feature dimensions: {feats[0].shape if feats else 'None'}")
            
            X = np.stack(feats, axis=0)
            probs = model.candidate_model.predict_proba(X)[:, 1]

            # Extra verbose: feature breakdown for each candidate (debug)
            try:
                for i, move in enumerate(legal_moves):
                    f = feats[i]
                    # General (11) + combo-specific (16)
                    general = f[:11]
                    combo = f[11:]
                    one_hot = combo[:7]
                    hybrid_rank = combo[7]
                    combo_length = combo[8]
                    breaks_flag = combo[9]
                    individual_strength = combo[10]
                    combo_type_multiplier = combo[11]
                    enhanced_breaks_penalty = combo[12]
                    combo_efficiency = combo[13]
                    combo_pref_bonus = combo[14]
                    combo_preserve_bonus = combo[15]
                    print(
                        f"🤖 [GeneralAdapter]   FeatBreakdown {i+1}: general={general.tolist()} | "
                        f"one_hot={one_hot.tolist()} hr={hybrid_rank:.3f} len={combo_length:.1f} "
                        f"breaks={breaks_flag:.1f} indiv={individual_strength:.3f} type_mul={combo_type_multiplier:.1f} "
                        f"enh_break={enhanced_breaks_penalty:.2f} eff={combo_efficiency:.3f} pref={combo_pref_bonus:.2f} "
                        f"preserve={combo_preserve_bonus:.2f}"
                    )
            except Exception:
                pass
            
            # Log all move scores
            print("🤖 [GeneralAdapter] Move scores:")
            for i, (move, prob) in enumerate(zip(legal_moves, probs)):
                move_type = move.get("type", "unknown")
                combo_type = move.get("combo_type", "unknown")
                rank_value = move.get("rank_value", -1)
                cards = move.get("cards", [])
                print(f"🤖 [GeneralAdapter]   Move {i+1}: {move_type} | {combo_type} | rank={rank_value} | cards={cards} | score={prob:.4f}")
            
            best_idx = int(np.argmax(probs))
            best = legal_moves[best_idx]
            best_score = probs[best_idx]
            
            print(f"🤖 [GeneralAdapter] Best move: {best} with score {best_score:.4f}")
            
            if best.get("type") == "play_cards":
                return {"type": "play_cards", "cards": best.get("cards", [])}
            return {"type": "pass", "cards": []}

        # Path B: fallback two-stage pipeline
        # If there is a last_move combo, filter by that combo_type, else use stage1 to pick combo type
        last_move = game_record.get("last_move") or {}
        combo_type = last_move.get("combo_type")
        filtered = []
        if combo_type:
            filtered = [m for m in legal_moves if m.get("combo_type") == combo_type]
        else:
            # stage1 features - fallback for old models
            rec = {
                "hand": game_record.get("hand", []),
                "cards_left": game_record.get("cards_left", []),
                "meta": {"legal_moves": legal_moves},
            }
            import numpy as np
            # Try new method first, fallback to old method
            if hasattr(model, 'extract_candidate_features'):
                # Use per-candidate approach even in fallback
                feats = [model.extract_candidate_features(rec, m) for m in legal_moves]
                if feats:
                    X = np.stack(feats, axis=0)
                    probs = model.candidate_model.predict_proba(X)[:, 1]
                    best_idx = int(np.argmax(probs))
                    best = legal_moves[best_idx]
                    if best.get("type") == "play_cards":
                        return {"type": "play_cards", "cards": best.get("cards", [])}
                    return {"type": "pass", "cards": []}
            elif hasattr(model, 'extract_stage1_features'):
                s1 = model.extract_stage1_features(rec)
                ct_id = model.stage1_model.predict(s1.reshape(1, -1))[0]
                # Map id back to string
                combo_types = getattr(model, "combo_types", ["single", "pair", "triple", "four_kind", "straight", "double_seq", "pass"])
                combo_type = combo_types[ct_id] if ct_id < len(combo_types) else "pass"
                if combo_type != "pass":
                    filtered = [m for m in legal_moves if m.get("combo_type") == combo_type]

        if not filtered:
            # Best-effort fallback: choose first playable
            for m in legal_moves:
                if m.get("type") == "play_cards" and m.get("cards"):
                    return {"type": "play_cards", "cards": m.get("cards")}
            return {"type": "pass", "cards": []}

        # Use simple strength ranking available in the model for Stage 2
        rankings = model.calculate_combo_strength_ranking(filtered)
        best_move = rankings[0]["move"] if rankings else filtered[0]
        if best_move.get("type") == "play_cards":
            return {"type": "play_cards", "cards": best_move.get("cards", [])}
        return {"type": "pass", "cards": []}


class BaoSamAdapter:
    """Adapter for Báo Sâm decisioning.

    Uses the new Unbeatable Sequence Model for intelligent decisions.
    Falls back to production rule-based provider if unavailable.
    """

    def __init__(self, use_unbeatable: bool = True) -> None:
        self._unbeatable_provider = None
        self._legacy_provider = None
        self.use_unbeatable = use_unbeatable

    def ensure_ready(self) -> bool:
        if self._unbeatable_provider is not None or self._legacy_provider is not None:
            return True
        
        # Try Unbeatable Sequence Model first
        if self.use_unbeatable:
            try:
                from ai_common.model_providers.unbeatable_bao_sam_provider import (  # type: ignore
                    get_unbeatable_bao_sam_provider,
                )
                self._unbeatable_provider = get_unbeatable_bao_sam_provider()
                if self._unbeatable_provider._ensure_loaded():
                    logger.info("BaoSamAdapter: Using Unbeatable Sequence Model")
                    return True
                else:
                    logger.warning("BaoSamAdapter: Unbeatable model failed to load, falling back to legacy")
            except Exception as e:
                logger.warning("BaoSamAdapter: Unbeatable model unavailable: %s", e)
        
        # Fallback to legacy provider
        try:
            from ai_common.model_providers.production_bao_sam_provider import (  # type: ignore
                get_production_bao_sam_provider,
            )
            self._legacy_provider = get_production_bao_sam_provider()
            logger.info("BaoSamAdapter: Using legacy production provider")
            return True
        except Exception as e:
            logger.warning("BaoSamAdapter: Legacy provider unavailable: %s", e)
            return False

    def should_declare(self, hand: List[int], player_count: int = 4) -> bool:
        if not self.ensure_ready():
            return False
        
        if self._unbeatable_provider is not None:
            dec = self._unbeatable_provider.predict_bao_sam_decision(hand, player_count)
            return bool(dec.get("should_declare"))
        elif self._legacy_provider is not None:
            dec = self._legacy_provider.predict_bao_sam_decision(hand, [])
            return bool(dec.get("should_declare"))
        
        return False
    
    def get_decision_details(self, hand: List[int], player_count: int = 4) -> Dict[str, Any]:
        """Get detailed decision information"""
        if not self.ensure_ready():
            return {
                'should_declare': False,
                'reason': 'adapter_not_ready',
                'model_type': 'none'
            }
        
        if self._unbeatable_provider is not None:
            result = self._unbeatable_provider.predict_bao_sam_decision(hand, player_count)
            result['model_type'] = 'unbeatable_sequence'
            return result
        elif self._legacy_provider is not None:
            result = self._legacy_provider.predict_bao_sam_decision(hand, [])
            result['model_type'] = 'legacy_production'
            return result
        
        return {
            'should_declare': False,
            'reason': 'no_provider_available',
            'model_type': 'none'
        }


