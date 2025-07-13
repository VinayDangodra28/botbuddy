#!/usr/bin/env python3
"""
Test script specifically for name interruption handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import *

def test_name_interruption():
    """Test the name interruption specifically"""
    
    print("🧪 TESTING NAME INTERRUPTION")
    print("=" * 40)
    
    # Simulate the scenario from your session
    current_stage = "policy_confirmation"  # Where the conversation should return
    user_input = "what is your name by the way"
    
    print(f"Current Stage: {current_stage}")
    print(f"User Input: \"{user_input}\"")
    
    # Test interruption detection
    is_interruption, detected_intent, confidence = interruption_handler.detect_interruption(
        user_input, current_stage
    )
    
    print(f"Interruption Detected: {is_interruption}")
    print(f"Detected Intent: {detected_intent}")
    print(f"Confidence: {confidence:.2f}")
    
    if is_interruption:
        # Test interruption handling
        response, metadata, should_resume = interruption_handler.handle_interruption(
            detected_intent, user_input, current_stage, session_data.copy(), user_data
        )
        
        print(f"Response: \"{response}\"")
        print(f"Should Resume: {should_resume}")
        print(f"Metadata: {metadata}")
        
        # Test the full conversation turn processing
        print("\n" + "-" * 40)
        print("FULL CONVERSATION TURN TEST:")
        
        bot_response, full_metadata, continues = process_conversation_turn(
            user_input, current_stage, user_data, session_data.copy()
        )
        
        print(f"Bot Response: \"{bot_response}\"")
        print(f"Final Stage: {full_metadata.get('update', {}).get('conversation_stage', 'No stage update')}")
        print(f"Returned to Main Flow: {full_metadata.get('returned_to_main_flow', False)}")
    
    print("\n" + "=" * 40)
    print("Expected behavior:")
    print("1. ✅ Should detect 'ask_agent_name' interruption")
    print("2. ✅ Should respond with name introduction")
    print("3. ✅ Should return to the same stage (policy_confirmation)")
    print("4. ✅ Should NOT create a new branch")

def test_conversation_flow():
    """Test the full conversation flow with interruption"""
    
    print("\n🎭 SIMULATED CONVERSATION WITH NAME INTERRUPTION")
    print("=" * 50)
    
    # Reset to a clean state
    test_session = {
        "conversation_stage": "policy_confirmation",
        "language_preference": "English",
        "chat_history": []
    }
    
    conversations = [
        ("Are these policy details correct?", "policy_confirmation"),  # Normal flow
        ("what is your name by the way", "policy_confirmation"),      # Interruption - should stay same
        ("yes", "policy_confirmation")                                # Continue from where left off
    ]
    
    for i, (user_input, expected_stage) in enumerate(conversations, 1):
        print(f"\nTurn {i}:")
        print(f"User: \"{user_input}\"")
        print(f"Expected to stay in stage: {expected_stage}")
        
        current_stage = test_session.get("conversation_stage")
        bot_response, metadata, continues = process_conversation_turn(
            user_input, current_stage, user_data, test_session
        )
        
        # Update session
        if "update" in metadata:
            for k, v in metadata["update"].items():
                test_session[k] = v
        
        print(f"Veena: \"{bot_response}\"")
        print(f"Actual stage: {test_session.get('conversation_stage')}")
        
        if test_session.get("conversation_stage") == expected_stage:
            print("✅ PASS - Correct stage maintained")
        else:
            print("❌ FAIL - Stage changed unexpectedly")
        
        if metadata.get("returned_to_main_flow"):
            print("✅ PASS - Returned to main flow correctly")

if __name__ == "__main__":
    test_name_interruption()
    test_conversation_flow()
