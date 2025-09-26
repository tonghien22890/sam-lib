#!/usr/bin/env python3
"""
Test script to demonstrate ai_common integration with model_build
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_unbeatable_integration():
    """Test Unbeatable Sequence Model integration"""
    print("🎯 Testing Unbeatable Sequence Model Integration")
    print("=" * 60)
    
    try:
        from ai_common.model_providers.unbeatable_bao_sam_provider import get_unbeatable_bao_sam_provider
        
        # Get provider
        provider = get_unbeatable_bao_sam_provider()
        print("✅ Provider initialized successfully")
        
        # Check model status
        status = provider.get_model_status()
        print(f"📊 Model Status: {status['status']}")
        print(f"📁 Model Directory: {status['model_dir']}")
        print(f"🤖 Generator Available: {status['generator_available']}")
        
        if status['trained_models']:
            print(f"🎓 Trained Models: {status['trained_models']}")
        else:
            print("⚠️  No trained models found (expected for fresh setup)")
        
        # Test decision making
        test_hands = [
            {'name': '🏆 PREMIUM: Quad 2s', 'hand': [12,25,38,51,11,24,37,10,23,36]},
            {'name': '💪 STRONG: Triples', 'hand': [11,24,37,10,23,36,9,22,35,8]},
            {'name': '❌ WEAK: Singles', 'hand': [0,1,2,3,4,5,6,7,8,9]}
        ]
        
        print("\n🧪 Testing Decision Making:")
        print("-" * 40)
        
        for test_case in test_hands:
            decision = provider.predict_bao_sam_decision(test_case['hand'], 4)
            result = "✅ DECLARE" if decision['should_declare'] else "❌ REJECT"
            print(f"{test_case['name']}: {result}")
            print(f"  Reason: {decision['reason']}")
            print(f"  Confidence: {decision['confidence']:.3f}")
            print()
        
        print("✅ Unbeatable integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Unbeatable integration test failed: {e}")
        return False

def test_general_integration():
    """Test General Gameplay Model integration"""
    print("\n🎮 Testing General Gameplay Model Integration")
    print("=" * 60)
    
    try:
        from ai_common.model_providers.enhanced_general_provider import GeneralPlayProvider
        
        # Get provider
        provider = GeneralPlayProvider()
        print("✅ General provider initialized successfully")
        
        # Check if model is ready
        ready = provider._ensure_loaded()
        print(f"📊 Model Ready: {ready}")
        
        if ready:
            print("✅ General model integration working!")
        else:
            print("⚠️  General model not available (expected if not trained)")
        
        return True
        
    except Exception as e:
        print(f"❌ General integration test failed: {e}")
        return False

def test_adapter_integration():
    """Test adapter integration"""
    print("\n🔌 Testing Adapter Integration")
    print("=" * 60)
    
    try:
        from ai_common.adapters.bot_adapter import BaoSamAdapter, GeneralAdapter
        
        # Test BaoSam adapter
        bao_sam_adapter = BaoSamAdapter()
        ready = bao_sam_adapter.ensure_ready()
        print(f"📊 BaoSam Adapter Ready: {ready}")
        
        if ready:
            # Test decision
            hand = [12,25,38,51,11,24,37,10,23,36]
            should_declare = bao_sam_adapter.should_declare(hand, 4)
            print(f"🎯 BaoSam Decision: {'DECLARE' if should_declare else 'REJECT'}")
            
            # Get detailed decision
            details = bao_sam_adapter.get_decision_details(hand, 4)
            print(f"📋 Model Type: {details.get('model_type', 'unknown')}")
        
        # Test General adapter
        general_adapter = GeneralAdapter()
        ready = general_adapter.ensure_ready()
        print(f"📊 General Adapter Ready: {ready}")
        
        print("✅ Adapter integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Adapter integration test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 AI Common Integration Test Suite")
    print("=" * 80)
    
    results = []
    
    # Test Unbeatable integration
    results.append(test_unbeatable_integration())
    
    # Test General integration
    results.append(test_general_integration())
    
    # Test Adapter integration
    results.append(test_adapter_integration())
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("✅ ai_common is successfully integrated with model_build")
    else:
        print("\n⚠️  Some tests failed - check the output above")
        print("💡 This is normal if models haven't been trained yet")
    
    print("\n📚 Next Steps:")
    print("1. Train models using scripts in model_build/scripts/")
    print("2. Use providers in your game system")
    print("3. Check INTEGRATION_GUIDE.md for detailed usage")

if __name__ == "__main__":
    main()
