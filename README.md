AI Common
=========

Shared utilities and abstractions used by AIs and the backend.

- Base strategies in `base_strategies/`
- Bot interfaces and implementations in `bots/`
- Model providers in `model_providers/` (integrates with model_build/)
- Adapters in `adapters/` (connects models to game system)
- JSONL data logger in `data_logger.py`
- Evaluators in `evaluators/`
- Short-term memory helpers in `memory/`
- Penalty avoidance helpers in `penalty_avoidance/`

Model Integration
-----------------
This package integrates with the models in `model_build/`:

- **General Gameplay**: Uses per-candidate XGBoost model for move selection
- **Báo Sâm (Unbeatable)**: Uses 3-phase ML pipeline for declaration decisions
- **Fallback**: Legacy rule-based providers for compatibility

Usage
-----
Import shared components from this package in the game backend or bots.

Example:
```python
from ai_common.bots.rule_based_bot import RuleBasedBot
from ai_common.model_providers.unbeatable_bao_sam_provider import get_unbeatable_bao_sam_provider
from ai_common.model_providers.enhanced_general_provider import GeneralPlayProvider

# Báo Sâm decisions
bao_sam_provider = get_unbeatable_bao_sam_provider()
decision = bao_sam_provider.predict_bao_sam_decision(hand, player_count)

# General gameplay
general_provider = GeneralPlayProvider()
move = general_provider.predict(game_record, legal_moves)
```


