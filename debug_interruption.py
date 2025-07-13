#!/usr/bin/env python3
"""
Debug interruption response handling
"""

import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from interruption_handler import InterruptionHandler
from branches_manager import BranchesManager

def debug_interruption_response():
    """Debug the interruption response handling"""
    
    branches_manager = BranchesManager("branches.json", "suggestions.json")
    interruption_handler = InterruptionHandler(branches_manager)
    
    # Set up the session data like in the test
    session_data = {
        "current_interruption": {
            "intent_name": "ask_agent_name",
            "original_stage": "policy_confirmation"
        }
    }
    
    user_input = "ok thanks"
    
    print("🔍 DEBUG: Checking interruption response matching")
    print(f"Session data: {json.dumps(session_data, indent=2)}")
    print(f"User input: '{user_input}'")
    
    # Check what interruption intents are loaded
    print(f"\n📋 Available interruption intents: {list(interruption_handler.interruptible_intents.keys())}")
    
    # Check the specific intent we're looking for
    intent_name = session_data["current_interruption"]["intent_name"]
    if intent_name in interruption_handler.interruptible_intents:
        intent_data = interruption_handler.interruptible_intents[intent_name]
        print(f"\n🎯 Intent '{intent_name}' data:")
        print(f"Expected responses: {json.dumps(intent_data.get('expected_user_responses', {}), indent=2)}")
    else:
        print(f"\n❌ Intent '{intent_name}' not found in interruptible_intents")
    
    # Test the response checking
    is_match, response_text, action, next_stage = interruption_handler.check_interruption_response(
        user_input, session_data
    )
    
    print(f"\n🔍 Response checking result:")
    print(f"Is match: {is_match}")
    print(f"Response text: {response_text}")
    print(f"Action: {action}")
    print(f"Next stage: {next_stage}")
    
    # Test the full response handling
    print(f"\n🔍 Full response handling:")
    response, metadata, should_continue = interruption_handler.handle_interruption_response(
        user_input, session_data, {"name": "Test User"}
    )
    
    print(f"Response: {response}")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
    print(f"Should continue: {should_continue}")

if __name__ == "__main__":
    debug_interruption_response()
