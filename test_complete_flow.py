#!/usr/bin/env python3
"""
Comprehensive test showing the complete interruption handling flow.
"""

import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import process_conversation_turn, session_data, user_data

def test_complete_interruption_flow():
    """Test a complete interruption flow from start to finish."""
    
    print("🧪 Complete Interruption Flow Test")
    print("=" * 60)
    
    # Reset session to policy_confirmation stage - clean slate
    session_data.clear()
    session_data.update({
        "conversation_stage": "policy_confirmation",
        "language_preference": "English",
        "chat_history": []
    })
    
    # Simulate the conversation flow
    steps = [
        {
            "step": 1,
            "description": "User is at policy_confirmation stage",
            "user_input": None,
            "action": "show_stage"
        },
        {
            "step": 2,
            "description": "User interrupts with agent name question",
            "user_input": "what's your name?",
            "expected": "Interruption detected and handled"
        },
        {
            "step": 3,
            "description": "User acknowledges agent name",
            "user_input": "ok thanks",
            "expected": "Interruption resolved, returned to policy_confirmation"
        },
        {
            "step": 4,
            "description": "User gives appropriate response for policy_confirmation",
            "user_input": "yes I want to reactivate",
            "expected": "Normal flow continues from policy_confirmation"
        }
    ]
    
    for step_info in steps:
        step_num = step_info["step"]
        description = step_info["description"]
        user_input = step_info["user_input"]
        
        print(f"\n🔹 Step {step_num}: {description}")
        print(f"Current stage: {session_data.get('conversation_stage')}")
        
        if step_info.get("action") == "show_stage":
            print("📍 Starting conversation at this stage")
            continue
            
        if user_input:
            print(f"User says: '{user_input}'")
            
            # Process the conversation turn
            current_stage = session_data.get("conversation_stage", "greeting")
            response, metadata, continues = process_conversation_turn(
                user_input, current_stage, user_data, session_data
            )
            
            print(f"🤖 Bot: {response[:100]}{'...' if len(response) > 100 else ''}")
            print(f"📊 Intent: {metadata.get('intent', 'None')}")
            print(f"📍 New stage: {session_data.get('conversation_stage')}")
            
            # Show key metadata
            if "interruption_resolved" in metadata:
                print(f"✅ Interruption resolved, restored to: {metadata.get('restored_to_stage')}")
            if "interruption_triggered" in metadata:
                print(f"🔔 Interruption triggered for: {metadata.get('original_stage')}")
            if "post_interruption_clarification" in metadata.get("intent", ""):
                print(f"🔄 Post-interruption clarification provided")
    
    print(f"\n🏁 Final state:")
    print(f"Conversation stage: {session_data.get('conversation_stage')}")
    print(f"In interruption: {'current_interruption' in session_data}")
    print(f"Returned from interruption: {session_data.get('returned_from_interruption', False)}")
    
    print("\n✅ Complete interruption flow test completed!")

if __name__ == "__main__":
    test_complete_interruption_flow()
