#!/usr/bin/env python3
"""
Two-Layer Adapter for ModelBot
Integrates FrameworkGenerator + StyleLearner for general gameplay
"""

import os
import sys
from typing import Dict, List, Any, Optional

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from model_build.scripts.two_layer.framework_generator import FrameworkGenerator
    from model_build.scripts.two_layer.style_learner import StyleLearner
except ImportError as e:
    print(f"⚠️ [TwoLayerAdapter] Import error: {e}")
    FrameworkGenerator = None
    StyleLearner = None


class TwoLayerAdapter:
    """
    Two-Layer Architecture Adapter
    Layer 1: FrameworkGenerator (rule-based sequence evaluation)
    Layer 2: StyleLearner (ML-based move selection)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.framework_generator = None
        self.style_learner = None
        try:
            self._debug = os.environ.get('ADAPTER_DEBUG', '0') == '1'
        except Exception:
            self._debug = False
        
        # Initialize FrameworkGenerator
        if FrameworkGenerator is not None:
            try:
                self.framework_generator = FrameworkGenerator()
                if self._debug:
                    print("✅ [TwoLayerAdapter] FrameworkGenerator initialized")
            except Exception as e:
                print(f"⚠️ [TwoLayerAdapter] FrameworkGenerator init failed: {e}")
        
        # Initialize StyleLearner
        if StyleLearner is not None:
            try:
                self.style_learner = StyleLearner()
                
                # Load trained model if path provided
                if model_path and os.path.exists(model_path):
                    self.style_learner.load(model_path)
                    if self._debug:
                        print(f"✅ [TwoLayerAdapter] StyleLearner loaded from {model_path}")
                    try:
                        mtime = os.path.getmtime(model_path)
                        if self._debug:
                            print(f"🕒 [TwoLayerAdapter] Model mtime: {mtime}")
                    except Exception:
                        pass
                else:
                    if self._debug:
                        print("⚠️ [TwoLayerAdapter] StyleLearner model not loaded - using fallback")
                    
            except Exception as e:
                print(f"⚠️ [TwoLayerAdapter] StyleLearner init failed: {e}")
    
    def predict(self, game_record: Dict[str, Any], legal_moves: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict best move using Two-Layer Architecture
        
        Args:
            game_record: Game state record
            legal_moves: List of legal moves
            
        Returns:
            Best move dict
        """
        try:
            # Layer 1: Generate framework from hand
            hand = game_record.get('hand', [])
            if not hand:
                if self._debug:
                    print("⚠️ [TwoLayerAdapter] No hand provided")
                return legal_moves[0] if legal_moves else {"type": "pass", "cards": []}
            
            if self.framework_generator is None:
                if self._debug:
                    print("⚠️ [TwoLayerAdapter] FrameworkGenerator not available")
                return legal_moves[0] if legal_moves else {"type": "pass", "cards": []}
            
            # Generate framework with top 3 sequences
            framework = self.framework_generator.generate_framework(hand)
            if self._debug:
                print(f"🎯 [TwoLayerAdapter] Framework generated: strength={framework.get('framework_strength', 0):.3f}, "
                      f"combos={len(framework.get('core_combos', []))}, "
                      f"alternatives={len(framework.get('alternative_sequences', []))}")

            # Debug ordering: show first 5 core combos and first 5 recommended moves
            core_preview = [
                {
                    'type': c.get('type'),
                    'len': len((c.get('cards') or [])),
                    'rank': c.get('rank_value'),
                    'pos': c.get('position', None)
                } for c in (framework.get('core_combos') or [])[:5]
            ]
            rec_preview = [
                {
                    'cards': m,
                    'len': len(m or [])
                } for m in (framework.get('recommended_moves') or [])[:5]
            ]
            if self._debug:
                print(f"🔎 [TwoLayerAdapter] Core combos(5): {core_preview}")
                print(f"🔎 [TwoLayerAdapter] Recommended(5): {rec_preview}")

            # Layer 2: Use StyleLearner to select best move
            if self.style_learner is not None and self.style_learner.model is not None:
                best_move = self.style_learner.predict_with_framework(game_record, legal_moves, framework)
                if self._debug:
                    print(f"🎯 [TwoLayerAdapter] StyleLearner prediction: {best_move}")
                return best_move
            else:
                # Fallback: use framework's recommended moves
                if self._debug:
                    print("⚠️ [TwoLayerAdapter] StyleLearner not available, using framework fallback")
                return self._fallback_prediction(legal_moves, framework)
                
        except Exception as e:
            print(f"❌ [TwoLayerAdapter] Error in prediction: {e}")
            import traceback
            traceback.print_exc()
            return legal_moves[0] if legal_moves else {"type": "pass", "cards": []}
    
    def _fallback_prediction(self, legal_moves: List[Dict[str, Any]], framework: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback prediction using framework recommendations"""
        recommended_moves = framework.get('recommended_moves', [])
        
        # Try to find a legal move that matches recommended moves
        for rec_move in recommended_moves:
            for legal_move in legal_moves:
                if (legal_move.get('type') == 'play_cards' and 
                    set(legal_move.get('cards', [])) == set(rec_move)):
                    if self._debug:
                        print(f"🎯 [TwoLayerAdapter] Fallback matched recommended move: {legal_move}")
                    return legal_move
        
        # If no match, use first legal move
        for move in legal_moves:
            if move.get('type') == 'play_cards':
                if self._debug:
                    print(f"🎯 [TwoLayerAdapter] Fallback to first legal move: {move}")
                return move
        
        # Last resort: pass
        if self._debug:
            print("🎯 [TwoLayerAdapter] Fallback to pass")
        return {"type": "pass", "cards": []}
    
    def get_framework_info(self, hand: List[int]) -> Dict[str, Any]:
        """Get framework information for debugging"""
        if self.framework_generator is None:
            return {"error": "FrameworkGenerator not available"}
        
        try:
            framework = self.framework_generator.generate_framework(hand)
            return {
                "framework_strength": framework.get('framework_strength', 0.0),
                "coverage_score": framework.get('coverage_score', 0.0),
                "end_rule_compliance": framework.get('end_rule_compliance', True),
                "combo_count": framework.get('combo_count', 0),
                "core_combos": len(framework.get('core_combos', [])),
                "alternative_sequences": len(framework.get('alternative_sequences', [])),
                "summary": self.framework_generator.get_framework_summary(framework)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def is_available(self) -> bool:
        """Check if Two-Layer Architecture is available"""
        return (self.framework_generator is not None and 
                self.style_learner is not None)