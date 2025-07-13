#!/usr/bin/env python3
"""
Test script for compound interruption handling.
Tests cases where user gives both a response AND an interruption in the same message.
"""

import json
import sys
from agent import process_conversation_turn, interruption_handler, user_data, session_data, save_session

def test_compound_interruption():
    """Test compound response + interruption handling"""
    
    # Test Case 1: "yes but from where did you get my number?"
    print("=" * 80)
    print("TEST CASE 1: Compound Response - Yes + Privacy Question")
    print("=" * 80)
    
    # Reset session data to intro_and_consent stage
    test_session = {
        "conversation_stage": "intro_and_consent",
        "language_preference": "English",
        "user_agreed_to_pay": None,
        "callback_scheduled": False,
        "chat_history": [],
        "last_intent": None
    }
    
    user_input = "yes but from where did you get my number?"
    current_stage = "intro_and_consent"
    
    print(f"Current Stage: {current_stage}")
    print(f"User Input: '{user_input}'")
    print("\n" + "-" * 60)
    
    # Test interruption detection directly
    print("🔍 Testing interruption detection...")
    is_interruption, intent_name, confidence = interruption_handler.detect_interruption(
        user_input, current_stage, confidence_threshold=0.4
    )
    print(f"Interruption detected: {is_interruption}")
    print(f"Intent: {intent_name}")
    print(f"Confidence: {confidence:.3f}")
    
    print("\n" + "-" * 60)
    print("🤖 Testing full conversation processing...")
    
    # Process the conversation turn
    bot_response, metadata, continues = process_conversation_turn(
        user_input, current_stage, user_data, test_session
    )
    
    print(f"\nBot Response:")
    print(f"'{bot_response}'")
    print(f"\nMetadata:")
    print(json.dumps(metadata, indent=2))
    print(f"\nConversation continues: {continues}")
    
    # Check if the response properly handled the interruption
    if "ValuEnable Life Insurance" in bot_response and "policy" in bot_response:
        print("\n✅ SUCCESS: Interruption properly handled - addressed privacy concern")
    else:
        print("\n❌ FAILURE: Interruption not handled - didn't address privacy concern")
    
    # Check if it's returning to main flow
    if metadata.get("interruption_handled") or metadata.get("returned_to_main_flow"):
        print("✅ SUCCESS: Marked as interruption handling")
    else:
        print("❌ FAILURE: Not marked as interruption handling")

def test_other_compound_cases():
    """Test other compound interruption cases"""
    
    test_cases = [
        {
            "name": "OK but what's your name?",
            "input": "ok but what's your name?",
            "stage": "policy_confirmation",
            "expected_intent": "ask_agent_name"
        },
        {
            "name": "Sure but I want to pay now",
            "input": "sure but I want to pay now", 
            "stage": "explain_policy_loss",
            "expected_intent": "early_payment_decision"
        },
        {
            "name": "Yes but I already paid",
            "input": "yes but I already paid",
            "stage": "policy_confirmation", 
            "expected_intent": "already_paid_interruption"
        },
        {
            "name": "Fine but call me later",
            "input": "fine but call me later",
            "stage": "intro_and_consent",
            "expected_intent": "reschedule_callback"
        }
    ]
    
    print("\n\n" + "=" * 80)
    print("ADDITIONAL COMPOUND RESPONSE TESTS")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print("-" * 40)
        
        # Test interruption detection
        is_interruption, intent_name, confidence = interruption_handler.detect_interruption(
            test_case["input"], test_case["stage"], confidence_threshold=0.4
        )
        
        print(f"Input: '{test_case['input']}'")
        print(f"Stage: {test_case['stage']}")
        print(f"Expected Intent: {test_case['expected_intent']}")
        print(f"Detected Intent: {intent_name}")
        print(f"Confidence: {confidence:.3f}")
        print(f"Is Interruption: {is_interruption}")
        
        if intent_name == test_case['expected_intent']:
            print("✅ SUCCESS: Correct intent detected")
        else:
            print("❌ FAILURE: Wrong intent detected")

if __name__ == "__main__":
    print("🧪 Testing Compound Interruption Handling")
    print("Testing cases where user gives response + interruption in same message")
    
    try:
        test_compound_interruption()
        test_other_compound_cases()
        
        print("\n\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print("If you see ✅ SUCCESS messages above, the compound interruption handling is working!")
        print("The system should now properly detect and handle interruptions even when")
        print("the user combines a response (yes/no/ok) with a question or concern.")
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
