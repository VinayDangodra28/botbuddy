#!/usr/bin/env python3
"""
Quick integration test for the updated agent with interruption handling.
"""

import json
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import (
    process_conversation_turn, 
    interruption_handler, 
    branches_manager
)

def test_agent_integration():
    """Test the full agent integration with interruption handling."""
    
    print("🧪 Testing Agent Integration with Interruption Handling")
    print("=" * 60)
    
    # Mock session data
    session_data = {
        "conversation_stage": "policy_confirmation",
        "language_preference": "English",
        "chat_history": []
    }
    
    # Mock user data
    user_data = {
        "name": "Test User",
        "policy_number": "12345",
        "premium_amount": "₹25,000"
    }
    
    test_scenarios = [
        {
            "name": "Normal interruption",
            "user_input": "what's your name",
            "expected_flow": "interruption"
        },
        {
            "name": "Follow-up to interruption",
            "user_input": "ok thanks",
            "setup_interruption": True,
            "expected_flow": "interruption_response"
        },
        {
            "name": "After interruption - should provide context",
            "user_input": "hmm okay",
            "setup_returned_flag": True,
            "expected_flow": "post_interruption_clarification"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Scenario {i}: {scenario['name']}")
        print("-" * 40)
        
        # Setup scenario
        if scenario.get("setup_interruption"):
            session_data["current_interruption"] = {
                "intent_name": "ask_agent_name",
                "original_stage": "policy_confirmation"
            }
            print("📋 Setup: In interruption flow")
        elif scenario.get("setup_returned_flag"):
            session_data["returned_from_interruption"] = True
            if "current_interruption" in session_data:
                del session_data["current_interruption"]
            print("📋 Setup: Just returned from interruption")
        else:
            # Clear any interruption state
            if "current_interruption" in session_data:
                del session_data["current_interruption"]
            session_data.pop("returned_from_interruption", None)
        
        try:
            # Process the conversation turn
            response, metadata, continues = process_conversation_turn(
                scenario["user_input"],
                session_data["conversation_stage"],
                user_data,
                session_data
            )
            
            print(f"📝 Response: {response[:100]}{'...' if len(response) > 100 else ''}")
            print(f"📊 Metadata keys: {list(metadata.keys())}")
            
            # Check expected flow
            expected = scenario["expected_flow"]
            if expected == "interruption":
                if "interruption_handled" in metadata:
                    print("✅ PASS: Interruption handled correctly")
                else:
                    print("❌ FAIL: Expected interruption handling")
                    
            elif expected == "interruption_response":
                if "interruption_resolved" in metadata or "interruption_response_handled" in metadata:
                    print("✅ PASS: Interruption response handled correctly")
                else:
                    print("❌ FAIL: Expected interruption response handling")
                    print(f"   Available metadata: {list(metadata.keys())}")
                    
            elif expected == "post_interruption_clarification":
                if metadata.get("intent") == "post_interruption_clarification":
                    print("✅ PASS: Post-interruption clarification provided (proper context recovery)")
                else:
                    print("❌ FAIL: Expected post-interruption clarification")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Integration Testing Complete!")

if __name__ == "__main__":
    test_agent_integration()
