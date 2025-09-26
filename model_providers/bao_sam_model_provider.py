"""
Báo Sâm Model Provider

This module provides Báo Sâm-specific model integration for the backend.
It handles both decision model (whether to declare Báo Sâm) and combo sequence model.
"""

import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Add model_build to path
sys.path.append(str(Path(__file__).parent.parent / "model_build"))

try:
    from model_build.bao_sam_models import BaoSamDecisionModel, BaoSamComboModel
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    print("⚠️  Báo Sâm models not available. Install model_build dependencies.")

class BaoSamModelProvider:
    """Provider for Báo Sâm models"""
    
    def __init__(self, models_dir: str = "model_build/runs"):
        self.models_dir = models_dir
        self.decision_model: Optional[BaoSamDecisionModel] = None
        self.combo_model: Optional[BaoSamComboModel] = None
        self.models_loaded = False
        
        if MODELS_AVAILABLE:
            self._load_models()
    
    def _load_models(self):
        """Load Báo Sâm models if available"""
        try:
            decision_model_path = os.path.join(self.models_dir, "bao_sam_decision_model.pkl")
            combo_model_path = os.path.join(self.models_dir, "bao_sam_combo_model.pkl")
            
            if os.path.exists(decision_model_path):
                self.decision_model = BaoSamDecisionModel()
                self.decision_model.load_model(decision_model_path)
                print(f"✅ Loaded Báo Sâm Decision Model from {decision_model_path}")
            else:
                print(f"⚠️  Báo Sâm Decision Model not found at {decision_model_path}")
            
            if os.path.exists(combo_model_path):
                self.combo_model = BaoSamComboModel()
                self.combo_model.load_model(combo_model_path)
                print(f"✅ Loaded Báo Sâm Combo Model from {combo_model_path}")
            else:
                print(f"⚠️  Báo Sâm Combo Model not found at {combo_model_path}")
            
            self.models_loaded = True
            
        except Exception as e:
            print(f"❌ Error loading Báo Sâm models: {e}")
            self.models_loaded = False
    
    def predict_bao_sam_decision(self, hand: List[int], sammove_sequence: List[Dict[str, Any]]) -> Tuple[bool, float]:
        """Predict whether to declare Báo Sâm"""
        if not self.models_loaded or not self.decision_model:
            return False, 0.0
        
        try:
            return self.decision_model.predict_bao_sam_decision(hand, sammove_sequence)
        except Exception as e:
            print(f"❌ Error predicting Báo Sâm decision: {e}")
            return False, 0.0
    
    def predict_next_combo(self, hand: List[int], current_combo: Dict[str, Any], 
                          sequence_position: int) -> Dict[str, Any]:
        """Predict next optimal combo in sequence"""
        if not self.models_loaded or not self.combo_model:
            return {"type": "pass", "cards": []}
        
        try:
            return self.combo_model.predict_next_combo(hand, current_combo, sequence_position)
        except Exception as e:
            print(f"❌ Error predicting next combo: {e}")
            return {"type": "pass", "cards": []}
    
    def is_available(self) -> bool:
        """Check if Báo Sâm models are available"""
        return self.models_loaded and (self.decision_model is not None or self.combo_model is not None)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "models_available": MODELS_AVAILABLE,
            "models_loaded": self.models_loaded,
            "decision_model_loaded": self.decision_model is not None,
            "combo_model_loaded": self.combo_model is not None,
            "models_dir": self.models_dir
        }

# Global instance
_bao_sam_provider = None

def get_bao_sam_provider() -> BaoSamModelProvider:
    """Get global Báo Sâm model provider instance"""
    global _bao_sam_provider
    if _bao_sam_provider is None:
        _bao_sam_provider = BaoSamModelProvider()
    return _bao_sam_provider
