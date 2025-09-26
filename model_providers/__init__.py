"""
Model Providers Module

This module contains model providers for AI decision-making:
- UnbeatableBaoSamProvider: Báo Sâm using Unbeatable Sequence Model
- EnhancedModelProvider: General gameplay provider (per-candidate)

Note: get_bao_sam_provider() returns the Unbeatable provider by default,
maintaining backward compatibility for web_backend/app.py imports.
"""

from .unbeatable_bao_sam_provider import get_unbeatable_bao_sam_provider  # type: ignore
from .enhanced_model_provider import EnhancedModelProvider  # type: ignore


def get_bao_sam_provider():
    """Backward-compatible export for web_backend/app.py

    Returns the Unbeatable Sequence Model-based provider.
    Falls back to legacy provider if Unbeatable model not available.
    """
    try:
        unbeatable_provider = get_unbeatable_bao_sam_provider()
        # Check if model is actually trained
        status = unbeatable_provider.get_model_status()
        if status.get('status') == 'ready':
            return unbeatable_provider
        else:
            print("⚠️  Unbeatable model not trained, falling back to legacy provider")
            from .production_bao_sam_provider import get_production_bao_sam_provider
            return get_production_bao_sam_provider()
    except Exception as e:
        print(f"⚠️  Unbeatable provider failed: {e}, falling back to legacy")
        from .production_bao_sam_provider import get_production_bao_sam_provider
        return get_production_bao_sam_provider()


__all__ = [
    'get_bao_sam_provider',
    'get_unbeatable_bao_sam_provider',
    'EnhancedModelProvider',
]
