# AI Common Integration Guide

This guide explains how `ai_common/` integrates with the `model_build/` solutions.

## Overview

The `ai_common/` package provides adapters and providers that connect the ML models in `model_build/` to the game system. It acts as a bridge between the game engine and the trained models.

## Model Integration

### 1. Unbeatable Sequence Model (Báo Sâm)

**Files:**
- `adapters/unbeatable_adapter.py` - Core adapter for the 3-phase ML pipeline
- `model_providers/unbeatable_bao_sam_provider.py` - Production provider

**Integration:**
```python
from ai_common.model_providers.unbeatable_bao_sam_provider import get_unbeatable_bao_sam_provider

# Get provider instance
provider = get_unbeatable_bao_sam_provider()

# Make Báo Sâm decision
decision = provider.predict_bao_sam_decision(hand, player_count)
print(f"Should declare: {decision['should_declare']}")
print(f"Unbeatable probability: {decision['unbeatable_probability']:.3f}")
print(f"User threshold: {decision['user_threshold']:.3f}")
```

**Model Requirements:**
- Requires trained models from `model_build/scripts/unbeatable/train_unbeatable_model.py`
- Models stored in `model_build/models/`:
  - `validation_model.pkl`
  - `pattern_model.pkl`
  - `threshold_model.pkl`

### 2. General Gameplay Model (Per-Candidate)

**Files:**
- `adapters/bot_adapter.py` - GeneralAdapter class
- `model_providers/enhanced_general_provider.py` - Production provider

**Integration:**
```python
from ai_common.model_providers.enhanced_general_provider import GeneralPlayProvider

# Get provider instance
provider = GeneralPlayProvider()

# Make move decision
move = provider.predict(game_record, legal_moves)
print(f"Selected move: {move}")
```

**Model Requirements:**
- Requires trained model from `model_build/scripts/general/train_optimized_model_v3.py`
- Model stored in `model_build/models/optimized_general_model_v3.pkl`

## Fallback Strategy

The integration includes fallback mechanisms:

1. **Unbeatable Model Fallback:**
   - If Unbeatable Sequence Model fails to load → Falls back to legacy rule-based provider
   - If no models available → Returns conservative decisions

2. **General Model Fallback:**
   - If per-candidate model fails → Falls back to two-stage pipeline
   - If no models available → Returns first available move

## Usage in Game System

### Bot Integration

```python
from ai_common.bots.model_bot import ModelBot
from ai_common.model_providers.unbeatable_bao_sam_provider import get_unbeatable_bao_sam_provider
from ai_common.model_providers.enhanced_general_provider import GeneralPlayProvider

class IntegratedBot(ModelBot):
    def __init__(self):
        super().__init__()
        self.bao_sam_provider = get_unbeatable_bao_sam_provider()
        self.general_provider = GeneralPlayProvider()
    
    def predict(self, game_record, legal_moves):
        # Use appropriate provider based on game type
        if game_record.get('game_type') == 'sam':
            return self.bao_sam_provider.predict(game_record, legal_moves)
        else:
            return self.general_provider.predict(game_record, legal_moves)
```

### Direct Adapter Usage

```python
from ai_common.adapters.unbeatable_adapter import UnbeatableAdapter
from ai_common.adapters.bot_adapter import GeneralAdapter

# Báo Sâm decisions
bao_sam_adapter = UnbeatableAdapter()
decision = bao_sam_adapter.should_declare_bao_sam(hand, player_count)

# General gameplay
general_adapter = GeneralAdapter()
move = general_adapter.predict(game_record, legal_moves)
```

## Model Status Checking

Both providers offer status checking:

```python
# Check Unbeatable model status
provider = get_unbeatable_bao_sam_provider()
status = provider.get_model_status()
print(f"Model loaded: {status['loaded']}")
print(f"Trained models: {status['trained_models']}")

# Check General model status
general_provider = GeneralPlayProvider()
ready = general_provider._ensure_loaded()
print(f"General model ready: {ready}")
```

## Error Handling

The integration includes comprehensive error handling:

1. **Import Errors:** Graceful fallback if model dependencies unavailable
2. **Model Loading Errors:** Fallback to rule-based providers
3. **Prediction Errors:** Return safe default decisions
4. **Path Resolution:** Automatic path setup for model imports

## Performance Considerations

1. **Lazy Loading:** Models loaded only when first used
2. **Singleton Pattern:** Providers cached to avoid reloading
3. **Fallback Caching:** Adapters cache fallback providers
4. **Error Logging:** Comprehensive logging for debugging

## Development Workflow

1. **Train Models:** Use scripts in `model_build/scripts/`
2. **Test Integration:** Use adapters directly for testing
3. **Deploy:** Use providers in production game system
4. **Monitor:** Check model status and accuracy stats

## Troubleshooting

### Common Issues

1. **Import Errors:**
   - Ensure `model_build/` is in Python path
   - Check that model files exist in `model_build/models/`

2. **Model Loading Failures:**
   - Verify model files are not corrupted
   - Check file permissions
   - Ensure all dependencies installed

3. **Fallback Activation:**
   - Check logs for fallback reasons
   - Verify model training completed successfully
   - Test with simple examples first

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed information about model loading, fallback activation, and decision making.
