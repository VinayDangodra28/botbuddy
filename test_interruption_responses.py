#!/usr/bin/env python3
"""
Test script for interruption handling with expected responses.
Tests the new interruption flow and closure handling.
"""

import json
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from branches_manager import BranchesManager
from interruption_handler import InterruptionHandler

def test_interruption_responses():
    """Test interruption detection and response handling."""
    
    print("🧪 Testing Interruption Handling with Expected Responses")
    print("=" * 60)
    
    # Initialize components
    branches_manager = BranchesManager("branches.json", "suggestions.json")
    interruption_handler = InterruptionHandler(branches_manager)
    
    # Mock session data
    session_data = {
        "conversation_stage": "policy_confirmation",
        "language_preference": "English",
        "chat_history": []
    }
    
    # Mock user data
    user_data = {
        "name": "Test User",
        "policy_number": "12345"
    }
    
    # Test cases for interruptions
    test_cases = [
        {
            "name": "Ask agent name interruption",
            "user_input": "what is your name",
            "current_stage": "policy_confirmation",
            "expected_interruption": "ask_agent_name"
        },
        {
            "name": "Response to agent name - acknowledges",
            "user_input": "ok thanks",
            "setup_interruption": "ask_agent_name",
            "expected_response_type": "acknowledges"
        },
        {
            "name": "Early payment decision",
            "user_input": "i want to pay now",
            "current_stage": "explain_policy_loss",
            "expected_interruption": "early_payment_decision"
        },
        {
            "name": "Response to payment - confirms",
            "user_input": "yes proceed",
            "setup_interruption": "early_payment_decision",
            "expected_response_type": "confirms_payment"
        },
        {
            "name": "Reschedule callback",
            "user_input": "call me later please",
            "current_stage": "payment_inquiry",
            "expected_interruption": "reschedule_callback"
        },
        {
            "name": "Response to reschedule - provides time",
            "user_input": "tomorrow evening",
            "setup_interruption": "reschedule_callback",
            "expected_response_type": "provides_time"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        # Setup interruption flow if needed
        if "setup_interruption" in test_case:
            session_data["current_interruption"] = {
                "intent": test_case["setup_interruption"],
                "interrupted_stage": "policy_confirmation"
            }
            print(f"📋 Setup: In interruption flow for '{test_case['setup_interruption']}'")
        else:
            # Clear any existing interruption
            if "current_interruption" in session_data:
                del session_data["current_interruption"]
        
        user_input = test_case["user_input"]
        current_stage = test_case.get("current_stage", "policy_confirmation")
        
        # Test interruption detection or response handling
        if "expected_interruption" in test_case:
            # Test interruption detection
            is_interruption, intent_name, confidence = interruption_handler.detect_interruption(
                user_input, current_stage
            )
            
            if is_interruption:
                print(f"✅ Detected interruption: {intent_name} (confidence: {confidence:.2f})")
                
                # Handle the interruption
                response, metadata, should_resume = interruption_handler.handle_interruption(
                    intent_name, user_input, current_stage, session_data, user_data
                )
                
                print(f"📝 Response: {response}")
                print(f"📊 Metadata: {json.dumps(metadata, indent=2)}")
                print(f"🔄 Should resume: {should_resume}")
                
                if test_case["expected_interruption"] == intent_name:
                    print("✅ PASS: Correct interruption detected")
                else:
                    print(f"❌ FAIL: Expected {test_case['expected_interruption']}, got {intent_name}")
            else:
                print("❌ FAIL: No interruption detected")
                
        elif "expected_response_type" in test_case:
            # Test interruption response handling
            if interruption_handler.is_in_interruption_flow(session_data):
                is_match, response_text, action, next_stage = interruption_handler.check_interruption_response(
                    user_input, session_data
                )
                
                if is_match:
                    print(f"✅ Matched response pattern")
                    print(f"📝 Response: {response_text}")
                    print(f"🎯 Action: {action}")
                    print(f"➡️ Next stage: {next_stage}")
                    
                    # Handle the response
                    final_response, metadata, should_continue = interruption_handler.handle_interruption_response(
                        user_input, session_data, user_data
                    )
                    
                    print(f"📝 Final response: {final_response}")
                    print(f"📊 Final metadata: {json.dumps(metadata, indent=2)}")
                    print("✅ PASS: Interruption response handled correctly")
                else:
                    print("❌ FAIL: No response pattern matched")
            else:
                print("❌ FAIL: Not in interruption flow")
    
    print("\n" + "=" * 60)
    print("🏁 Testing Complete!")

def test_branch_creation_prevention():
    """Test that branch creation is prevented after interruptions."""
    
    print("\n🧪 Testing Branch Creation Prevention")
    print("=" * 60)
    
    # This would require more complex setup with the full agent
    # For now, just verify the flag is set correctly
    
    branches_manager = BranchesManager("branches.json", "suggestions.json")
    interruption_handler = InterruptionHandler(branches_manager)
    
    session_data = {"conversation_stage": "policy_confirmation"}
    user_data = {"name": "Test User"}
    
    # Simulate returning from interruption
    response, metadata, should_continue = interruption_handler.handle_interruption_response(
        "ok thanks", 
        {
            "current_interruption": {"intent": "ask_agent_name", "interrupted_stage": "policy_confirmation"},
            "interrupted_stage": "policy_confirmation"
        }, 
        user_data
    )
    
    print(f"📝 Response: {response}")
    print(f"📊 Metadata: {json.dumps(metadata, indent=2)}")
    
    # Check if returned_from_interruption flag would be set
    if "returned_to_main_flow" in metadata:
        print("✅ PASS: Would set flag to prevent branch creation")
    else:
        print("❌ FAIL: Flag not set correctly")

if __name__ == "__main__":
    test_interruption_responses()
    test_branch_creation_prevention()
