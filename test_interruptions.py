#!/usr/bin/env python3
"""
Demo script to test the interruption handling system in Veena.
This script demonstrates various interruption scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import *

def test_interruption_scenarios():
    """Test various interruption scenarios"""
    
    print("🧪 TESTING INTERRUPTION HANDLING SYSTEM")
    print("=" * 50)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Repeat Request",
            "current_stage": "policy_confirmation", 
            "user_input": "Can you repeat that please?",
            "expected_intent": "request_repeat"
        },
        {
            "name": "New Policy Question",
            "current_stage": "payment_inquiry",
            "user_input": "Can I buy a new policy instead?", 
            "expected_intent": "ask_about_other_policies"
        },
        {
            "name": "Callback Request", 
            "current_stage": "explain_policy_loss",
            "user_input": "Please call me later",
            "expected_intent": "reschedule_callback"
        },
        {
            "name": "Privacy Concern",
            "current_stage": "greeting",
            "user_input": "How did you get my number?",
            "expected_intent": "ask_how_you_got_number"
        },
        {
            "name": "Early Payment Decision",
            "current_stage": "policy_confirmation",
            "user_input": "I want to pay now",
            "expected_intent": "early_payment_decision"
        },
        {
            "name": "Language Switch",
            "current_stage": "payment_inquiry", 
            "user_input": "Hindi mein baat karte hai",
            "expected_intent": "language_switch_request"
        },
        {
            "name": "Complaint/Angry",
            "current_stage": "intro_and_consent",
            "user_input": "I'm frustrated with your service",
            "expected_intent": "complaint_or_angry"
        },
        {
            "name": "Already Paid",
            "current_stage": "payment_inquiry",
            "user_input": "I already paid last week", 
            "expected_intent": "already_paid_interruption"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 Test {i}: {test_case['name']}")
        print("-" * 30)
        print(f"Current Stage: {test_case['current_stage']}")
        print(f"User Input: \"{test_case['user_input']}\"")
        
        # Test interruption detection
        is_interruption, detected_intent, confidence = interruption_handler.detect_interruption(
            test_case['user_input'], 
            test_case['current_stage']
        )
        
        print(f"Interruption Detected: {is_interruption}")
        print(f"Detected Intent: {detected_intent}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Expected Intent: {test_case['expected_intent']}")
        
        # Check if detection matches expectation
        if detected_intent == test_case['expected_intent']:
            print("✅ PASS - Correct intent detected")
        else:
            print("❌ FAIL - Intent mismatch")
        
        # Test interruption handling if detected
        if is_interruption:
            try:
                response, metadata, should_resume = interruption_handler.handle_interruption(
                    detected_intent, 
                    test_case['user_input'],
                    test_case['current_stage'],
                    session_data.copy(),  # Use copy to avoid modifying original
                    user_data
                )
                print(f"Response: \"{response}\"")
                print(f"Should Resume: {should_resume}")
                print(f"Critical Interruption: {interruption_handler.is_critical_interruption(detected_intent)}")
            except Exception as e:
                print(f"❌ Error in handling: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 INTERRUPTION SYSTEM DEMO COMPLETE")
    print("\nKey Features Demonstrated:")
    print("• ✅ Keyword-based interruption detection")
    print("• ✅ Confidence scoring and thresholds") 
    print("• ✅ Context-aware interruption handling")
    print("• ✅ Critical vs non-critical interruption classification")
    print("• ✅ Conversation flow resumption")
    print("• ✅ Multi-stage interruption compatibility")

def demo_conversation_with_interruptions():
    """Demo a conversation flow with interruptions"""
    
    print("\n🎭 INTERACTIVE DEMO - Conversation with Interruptions")
    print("=" * 60)
    print("Type 'quit' to exit, 'test' to run automated tests")
    print("Try these interruption examples:")
    print("• 'repeat that please'")
    print("• 'can I buy a new policy?'") 
    print("• 'call me later'")
    print("• 'how did you get my number?'")
    print("• 'I want to pay now'")
    print("• 'hindi mein baat karte hai'")
    print("• 'I'm angry about this'")
    print("• 'I already paid'")
    print("-" * 60)
    
    # Reset session to greeting for demo
    session_data["conversation_stage"] = "greeting"
    session_data["chat_history"] = []
    
    while True:
        current_stage = session_data.get("conversation_stage", "greeting")
        print(f"\n[Current Stage: {current_stage}]")
        
        user_input = input("👤 You: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'test':
            test_interruption_scenarios()
            continue
        elif not user_input:
            continue
        
        # Process with interruption handling
        bot_response, metadata, continues = process_conversation_turn(
            user_input, current_stage, user_data, session_data
        )
        
        print(f"🤖 Veena: {bot_response}")
        
        # Update session
        if "update" in metadata:
            for k, v in metadata["update"].items():
                session_data[k] = v
        if "intent" in metadata:
            session_data["last_intent"] = metadata["intent"]
        
        # Add to history
        session_data.setdefault("chat_history", []).append({
            "user": user_input,
            "veena": bot_response
        })
        
        if session_data.get("conversation_stage") == "closure":
            print("✅ Conversation completed!")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_interruption_scenarios()
    else:
        demo_conversation_with_interruptions()
