#!/usr/bin/env python3
"""
Real-world test for the specific case that was failing.
Simulates the exact conversation flow that was problematic.
"""

import json
import sys
from agent import process_conversation_turn, interruption_handler, user_data, session_data, save_session

def test_real_world_scenario():
    """Test the exact scenario that was failing"""
    
    print("=" * 80)
    print("REAL-WORLD SCENARIO TEST")
    print("Simulating: User says 'yes but from where did you get my number?'")
    print("At intro_and_consent stage")
    print("=" * 80)
    
    # Setup session data to match the real scenario
    test_session = {
        "conversation_stage": "intro_and_consent",
        "language_preference": "English",
        "user_agreed_to_pay": None,
        "callback_scheduled": False,
        "user_reason_for_non_payment": None,
        "last_intent": "initial_greeting",
        "chat_history": [
            {
                "user": None,
                "veena": "Hello and very Good Morning Sir, May I speak with Pratik Jadhav?\n\n\n```json\n{\n  \"intent\": \"initial_greeting\",\n  \"update\": {\n    \"conversation_stage\": \"greeting\",\n    \"language_preference\": \"English\",\n    \"user_reason_for_non_payment\": null\n  }\n}\n```\n"
            }
        ]
    }
    
    user_input = "yes but from where did you get my number?"
    current_stage = "intro_and_consent"
    
    print(f"📍 Current Stage: {current_stage}")
    print(f"👤 User Input: '{user_input}'")
    print(f"🎯 Expected: Should handle as interruption (privacy question)")
    print(f"❌ Previous Behavior: Was treating as just 'yes' and moving to next stage")
    print(f"✅ Fixed Behavior: Should address privacy concern and stay in same stage")
    
    print("\n" + "-" * 60)
    print("🧪 PROCESSING CONVERSATION TURN...")
    print("-" * 60)
    
    # Process the conversation
    bot_response, metadata, continues = process_conversation_turn(
        user_input, current_stage, user_data, test_session
    )
    
    print(f"\n🤖 Bot Response:")
    print(f"'{bot_response}'")
    
    print(f"\n📊 Metadata:")
    print(json.dumps(metadata, indent=2))
    
    print(f"\n🔄 Conversation continues: {continues}")
    
    # Analyze the results
    print("\n" + "=" * 60)
    print("ANALYSIS OF RESULTS")
    print("=" * 60)
    
    success_count = 0
    total_checks = 4
    
    # Check 1: Was interruption detected?
    if metadata.get("interruption_handled"):
        print("✅ CHECK 1: Interruption was properly detected and handled")
        success_count += 1
    else:
        print("❌ CHECK 1: Interruption was NOT detected - this is the bug!")
    
    # Check 2: Did it address privacy concern?
    if "ValuEnable Life Insurance" in bot_response and ("records" in bot_response or "policy" in bot_response):
        print("✅ CHECK 2: Privacy concern was addressed in response")
        success_count += 1
    else:
        print("❌ CHECK 2: Privacy concern was NOT addressed")
    
    # Check 3: Did it stay in the same stage?
    new_stage = metadata.get("update", {}).get("conversation_stage")
    if new_stage == current_stage:
        print(f"✅ CHECK 3: Correctly stayed in same stage ({current_stage})")
        success_count += 1
    else:
        print(f"❌ CHECK 3: Incorrectly moved to different stage ({new_stage})")
    
    # Check 4: Did it mark for return to main flow?
    if metadata.get("returned_to_main_flow"):
        print("✅ CHECK 4: Marked to return to main conversation flow")
        success_count += 1
    else:
        print("❌ CHECK 4: Did NOT mark to return to main flow")
    
    print(f"\n📈 OVERALL RESULT: {success_count}/{total_checks} checks passed")
    
    if success_count == total_checks:
        print("🎉 SUCCESS: All checks passed! The compound interruption handling is working correctly.")
        print("👍 The original issue has been resolved.")
    else:
        print(f"⚠️  PARTIAL SUCCESS: {success_count} out of {total_checks} checks passed.")
        print("🔧 Some aspects still need improvement.")

if __name__ == "__main__":
    print("🧪 Testing Real-World Compound Interruption Scenario")
    
    try:
        test_real_world_scenario()
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
