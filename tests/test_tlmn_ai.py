"""
Test TLMN AI Implementation

Comprehensive tests for TLMN AI components including
strategies, providers, adapters, and bots.
"""

import unittest
import sys
import os
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from ai_common.strategies.tlmn_strategy import TLMNStrategy
from ai_common.model_providers.tlmn_general_provider import TLMNGeneralProvider
from ai_common.adapters.tlmn_adapter import TLMNAdapter
from ai_common.bots.tlmn_bot import TLMNBot
from ai_common.bots.bot_interface import GameState, BotDecision


class TestTLMNStrategy(unittest.TestCase):
    """Test TLMN strategy implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.strategy = TLMNStrategy()
        self.game_state = {
            'hand': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'current_player_id': 0,
            'round_id': 1,
            'turn_id': 1,
            'tlmn_state': {
                'color_penalties': {},
                'chat_rewards': {},
                'special_events': {},
                'cards_played_count': {},
                'is_ket_3_bich': False,
                'ket_3_bich_player': None
            }
        }
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        self.assertEqual(self.strategy.config.name, "tlmn_strategy")
        self.assertEqual(self.strategy.config.game_type, "tlmn")
        self.assertEqual(self.strategy.config.aggressiveness, 0.6)
        self.assertEqual(self.strategy.config.risk_tolerance, 0.7)
    
    def test_evaluate_move(self):
        """Test move evaluation"""
        move = {
            'type': 'play_cards',
            'cards': [0, 1, 2],
            'combo_type': 'triple',
            'rank_value': 0
        }
        
        score = self.strategy.evaluate_move(move, self.game_state)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_select_best_move(self):
        """Test best move selection"""
        legal_moves = [
            {'type': 'play_cards', 'cards': [0, 1, 2], 'combo_type': 'triple', 'rank_value': 0},
            {'type': 'play_cards', 'cards': [3, 4], 'combo_type': 'pair', 'rank_value': 1},
            {'type': 'pass', 'cards': []}
        ]
        
        best_move = self.strategy.select_best_move(legal_moves, self.game_state)
        self.assertIsInstance(best_move, dict)
        self.assertIn('type', best_move)
    
    def test_should_declare_special(self):
        """Test special declaration (TLMN doesn't have Báo Sâm)"""
        result = self.strategy.should_declare_special(self.game_state)
        self.assertFalse(result)  # TLMN doesn't have Báo Sâm
    
    def test_tlmn_end_rules(self):
        """Test TLMN end rule violations"""
        # Test ending with 2
        move_with_2 = {
            'type': 'play_cards',
            'cards': [12],  # 2 card
            'combo_type': 'single',
            'rank_value': 12
        }
        
        # Mock game state where this would be the last move
        end_game_state = self.game_state.copy()
        end_game_state['hand'] = [12]  # Only 2 card left
        
        violates = self.strategy._violates_tlmn_end_rules(move_with_2, end_game_state)
        self.assertTrue(violates)
    
    def test_four_of_a_kind_detection(self):
        """Test four-of-a-kind detection"""
        # Test valid four-of-a-kind
        four_kind = [0, 13, 26, 39]  # All Aces
        self.assertTrue(self.strategy._is_four_of_a_kind(four_kind))
        
        # Test invalid four-of-a-kind
        not_four_kind = [0, 1, 2, 3]  # Different ranks
        self.assertFalse(self.strategy._is_four_of_a_kind(not_four_kind))
    
    def test_2_card_detection(self):
        """Test 2 card detection"""
        # Test 2 cards
        self.assertTrue(self.strategy._is_2_card(12))  # 2♠
        self.assertTrue(self.strategy._is_2_card(25))  # 2♥
        self.assertTrue(self.strategy._is_2_card(38))  # 2♦
        self.assertTrue(self.strategy._is_2_card(51))  # 2♣
        
        # Test non-2 cards
        self.assertFalse(self.strategy._is_2_card(0))   # Ace
        self.assertFalse(self.strategy._is_2_card(1))    # 3
        self.assertFalse(self.strategy._is_2_card(11))  # King


class TestTLMNProvider(unittest.TestCase):
    """Test TLMN provider implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.provider = TLMNGeneralProvider()
        self.game_record = {
            'hand': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'cards_left': [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
            'current_player_id': 0,
            'round_id': 1,
            'turn_id': 1,
            'tlmn_state': {
                'color_penalties': {},
                'chat_rewards': {},
                'special_events': {},
                'cards_played_count': {},
                'is_ket_3_bich': False,
                'ket_3_bich_player': None
            }
        }
        self.legal_moves = [
            {'type': 'play_cards', 'cards': [0, 1, 2], 'combo_type': 'triple', 'rank_value': 0},
            {'type': 'play_cards', 'cards': [3, 4], 'combo_type': 'pair', 'rank_value': 1},
            {'type': 'pass', 'cards': []}
        ]
    
    def test_provider_initialization(self):
        """Test provider initialization"""
        self.assertEqual(self.provider.name, "tlmn_general_play")
        self.assertEqual(self.provider.version, "v1")
        self.assertEqual(self.provider.game_type, "tlmn")
    
    def test_predict(self):
        """Test prediction with TLMN logic"""
        prediction = self.provider.predict(self.game_record, self.legal_moves)
        self.assertIsInstance(prediction, dict)
        self.assertIn('type', prediction)
    
    def test_get_tlmn_features(self):
        """Test TLMN feature extraction"""
        features = self.provider.get_tlmn_features(self.game_record)
        self.assertIsInstance(features, dict)
        self.assertIn('color_penalties', features)
        self.assertIn('chat_rewards', features)
        self.assertIn('special_events', features)
        self.assertIn('cards_played_count', features)
        self.assertIn('is_ket_3_bich', features)
        self.assertIn('ket_3_bich_player', features)


class TestTLMNAdapter(unittest.TestCase):
    """Test TLMN adapter implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.adapter = TLMNAdapter()
        self.game_record = {
            'hand': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'cards_left': [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
            'current_player_id': 0,
            'round_id': 1,
            'turn_id': 1,
            'tlmn_state': {
                'color_penalties': {},
                'chat_rewards': {},
                'special_events': {},
                'cards_played_count': {},
                'is_ket_3_bich': False,
                'ket_3_bich_player': None
            }
        }
        self.legal_moves = [
            {'type': 'play_cards', 'cards': [0, 1, 2], 'combo_type': 'triple', 'rank_value': 0},
            {'type': 'play_cards', 'cards': [3, 4], 'combo_type': 'pair', 'rank_value': 1},
            {'type': 'pass', 'cards': []}
        ]
    
    def test_adapter_initialization(self):
        """Test adapter initialization"""
        self.assertEqual(self.adapter.game_type, "tlmn")
    
    def test_predict(self):
        """Test prediction with TLMN adapter"""
        prediction = self.adapter.predict(self.game_record, self.legal_moves)
        self.assertIsInstance(prediction, dict)
        self.assertIn('type', prediction)
    
    def test_extract_tlmn_features(self):
        """Test TLMN feature extraction"""
        features = self.adapter._extract_tlmn_features(self.game_record)
        self.assertIsInstance(features, dict)
        self.assertIn('color_penalties', features)
        self.assertIn('chat_rewards', features)
        self.assertIn('special_events', features)
        self.assertIn('cards_played_count', features)
        self.assertIn('is_ket_3_bich', features)
        self.assertIn('ket_3_bich_player', features)
        self.assertIn('round_id', features)
        self.assertIn('turn_id', features)
    
    def test_filter_tlmn_moves(self):
        """Test TLMN move filtering"""
        filtered_moves = self.adapter._filter_tlmn_moves(self.legal_moves, self.game_record)
        self.assertIsInstance(filtered_moves, list)
        self.assertLessEqual(len(filtered_moves), len(self.legal_moves))
    
    def test_is_valid_tlmn_move(self):
        """Test TLMN move validation"""
        valid_move = {'type': 'play_cards', 'cards': [0, 1, 2], 'combo_type': 'triple', 'rank_value': 0}
        invalid_move = {'type': 'play_cards', 'cards': [12], 'combo_type': 'single', 'rank_value': 12}
        
        # Mock game state where invalid move would be last move
        end_game_state = self.game_record.copy()
        end_game_state['hand'] = [12]
        
        self.assertTrue(self.adapter._is_valid_tlmn_move(valid_move, self.game_record))
        self.assertFalse(self.adapter._is_valid_tlmn_move(invalid_move, end_game_state))


class TestTLMNBot(unittest.TestCase):
    """Test TLMN bot implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = TLMNBot(bot_id=1, name="Test TLMN Bot")
        self.game_state = GameState(
            current_player_id=0,
            hand=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            legal_moves=[
                {'type': 'play_cards', 'cards': [0, 1, 2], 'combo_type': 'triple', 'rank_value': 0},
                {'type': 'play_cards', 'cards': [3, 4], 'combo_type': 'pair', 'rank_value': 1},
                {'type': 'pass', 'cards': []}
            ],
            can_pass=True,
            game_record={
                'tlmn_state': {
                    'color_penalties': {},
                    'chat_rewards': {},
                    'special_events': {},
                    'cards_played_count': {},
                    'is_ket_3_bich': False,
                    'ket_3_bich_player': None
                }
            },
            round_info={'round_id': 1, 'turn_id': 1}
        )
    
    def test_bot_initialization(self):
        """Test bot initialization"""
        self.assertEqual(self.bot.bot_id, 1)
        self.assertEqual(self.bot.name, "Test TLMN Bot")
        self.assertIsNotNone(self.bot.strategy)
        self.assertIsNotNone(self.bot.provider)
    
    def test_choose_move(self):
        """Test move selection"""
        decision = self.bot.choose_move(self.game_state)
        self.assertIsInstance(decision, BotDecision)
        self.assertIn(decision.action, ['play_cards', 'pass'])
        self.assertIsInstance(decision.confidence, float)
        self.assertIsInstance(decision.reasoning, str)
        self.assertIsInstance(decision.metadata, dict)
    
    def test_should_declare_bao_sam(self):
        """Test Báo Sâm declaration (TLMN doesn't have Báo Sâm)"""
        result = self.bot.should_declare_bao_sam([0, 1, 2, 3, 4], 4)
        self.assertFalse(result)  # TLMN doesn't have Báo Sâm
    
    def test_get_bot_info(self):
        """Test bot information"""
        info = self.bot.get_bot_info()
        self.assertIsInstance(info, dict)
        self.assertEqual(info['bot_id'], 1)
        self.assertEqual(info['name'], "Test TLMN Bot")
        self.assertEqual(info['game_type'], 'tlmn')
        self.assertIn('strategy', info)
        self.assertIn('provider', info)
        self.assertIn('capabilities', info)
    
    def test_reset(self):
        """Test bot reset"""
        # Add some memory
        self.bot.update_memory({'type': 'test_event', 'data': 'test'})
        self.bot._decision_history.append({'test': 'decision'})
        
        # Reset
        self.bot.reset()
        
        # Check that memory is cleared
        self.assertEqual(len(self.bot._game_memory), 0)
        self.assertEqual(len(self.bot._decision_history), 0)
    
    def test_update_memory(self):
        """Test memory update"""
        event = {'type': 'test_event', 'data': 'test_data'}
        self.bot.update_memory(event)
        
        self.assertIn('test_event', self.bot._game_memory)
        self.assertEqual(len(self.bot._game_memory['test_event']), 1)
        self.assertEqual(self.bot._game_memory['test_event'][0], event)
    
    def test_fallback_decision(self):
        """Test fallback decision creation"""
        # Create empty game state to trigger fallback
        empty_game_state = GameState(
            current_player_id=0,
            hand=[],
            legal_moves=[],
            can_pass=False,
            game_record={},
            round_info={}
        )
        
        decision = self.bot._create_fallback_decision(empty_game_state)
        self.assertIsInstance(decision, BotDecision)
        self.assertEqual(decision.action, 'pass')
        self.assertTrue(decision.metadata.get('fallback', False))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
