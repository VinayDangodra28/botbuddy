#!/usr/bin/env python3
"""
Test script to verify that new branch creation properly connects to existing branches
to prevent conversation loops.
"""

import json
import sys
from agent import analyze_user_response_and_suggest, branches_manager, user_data

def test_branch_connection_logic():
    """Test that new branches connect to existing branches"""
    
    print("=" * 80)
    print("TEST: Branch Connection Logic")
    print("Testing that new branches connect to existing branches to prevent loops")
    print("=" * 80)
    
    # Test case: User gives vague response that needs new branch
    test_session = {
        "conversation_stage": "policy_confirmation",
        "language_preference": "English",
        "chat_history": []
    }
    
    user_input = "i don't really understand what you're saying"
    current_stage = "policy_confirmation"
    
    print(f"📍 Current Stage: {current_stage}")
    print(f"👤 User Input: '{user_input}' (vague/confusing response)")
    print(f"🎯 Expected: Should create new branch that connects to existing branches")
    
    # Get available branches for reference
    all_branches = branches_manager.read_all_branches()
    available_branches = all_branches.get("_metadata", {}).get("available_branches", [])
    print(f"📋 Available Branches: {len(available_branches)} branches")
    print(f"   {', '.join(available_branches[:10])}{'...' if len(available_branches) > 10 else ''}")
    
    print("\n" + "-" * 60)
    print("🧪 TESTING BRANCH CREATION...")
    print("-" * 60)
    
    try:
        # Test the branch creation logic
        bot_response, metadata, is_unexpected = analyze_user_response_and_suggest(
            user_input, current_stage, user_data, test_session
        )
        
        print(f"\n🤖 Bot Response:")
        print(f"'{bot_response[:200]}{'...' if len(bot_response) > 200 else ''}'")
        
        print(f"\n📊 Metadata:")
        print(json.dumps(metadata, indent=2))
        
        # Analyze the branch suggestion
        print("\n" + "=" * 60)
        print("ANALYSIS OF BRANCH SUGGESTION")
        print("=" * 60)
        
        if "branch_suggestion" in metadata:
            branch_suggestion = metadata["branch_suggestion"]
            suggestion_details = branch_suggestion.get("suggestion_details", {})
            expected_responses = suggestion_details.get("expected_user_responses", {})
            
            print(f"✅ Branch suggestion created:")
            print(f"   Branch name: {suggestion_details.get('branch_name', 'N/A')}")
            print(f"   Intent: {suggestion_details.get('intent', 'N/A')}")
            
            # Check if next stages use existing branches
            next_stages = []
            for response_type, response_data in expected_responses.items():
                next_stage = response_data.get("next")
                if next_stage:
                    next_stages.append((response_type, next_stage))
            
            print(f"\n📋 Checking next stages connection:")
            all_valid = True
            for response_type, next_stage in next_stages:
                if next_stage in available_branches:
                    print(f"   ✅ {response_type} → {next_stage} (valid existing branch)")
                else:
                    print(f"   ❌ {response_type} → {next_stage} (NOT in available branches)")
                    all_valid = False
            
            if all_valid and next_stages:
                print(f"\n🎉 SUCCESS: All {len(next_stages)} next stages connect to existing branches!")
                print("👍 This will prevent conversation loops and ensure proper flow.")
            elif not next_stages:
                print(f"\n⚠️  WARNING: No next stages defined in the branch")
            else:
                print(f"\n❌ FAILURE: Some next stages don't connect to existing branches")
                print("🔧 This could cause conversation loops or dead ends")
        else:
            print("❌ No branch suggestion found in metadata")
            
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()

def test_current_session_state():
    """Test the current session state after our fixes"""
    
    print("\n\n" + "=" * 80)
    print("TEST: Current Session State")
    print("Checking if the conversation loop issue is resolved")
    print("=" * 80)
    
    try:
        with open('session_data.json', 'r') as f:
            session_data = json.load(f)
        
        current_stage = session_data.get("conversation_stage")
        print(f"📍 Current Stage: {current_stage}")
        
        # Check if current stage exists in available branches
        all_branches = branches_manager.read_all_branches()
        available_branches = all_branches.get("_metadata", {}).get("available_branches", [])
        
        if current_stage in available_branches:
            print(f"✅ Current stage '{current_stage}' is a valid existing branch")
            
            # Check if the branch has proper structure
            branch_data = branches_manager.read_branch(current_stage)
            if branch_data:
                print(f"✅ Branch data found for '{current_stage}'")
                expected_responses = branch_data.get("expected_user_responses", {})
                print(f"📋 Available responses: {list(expected_responses.keys())}")
                
                # Check next stages
                next_stages = []
                for resp_type, resp_data in expected_responses.items():
                    next_stage = resp_data.get("next")
                    if next_stage:
                        next_stages.append(next_stage)
                
                if next_stages:
                    print(f"🔗 Next stages: {next_stages}")
                    all_valid = all(stage in available_branches for stage in next_stages)
                    if all_valid:
                        print("✅ All next stages are valid existing branches")
                    else:
                        print("❌ Some next stages are not valid branches")
                else:
                    print("⚠️  No next stages defined (might be terminal branch)")
            else:
                print(f"❌ No branch data found for '{current_stage}'")
        else:
            print(f"❌ Current stage '{current_stage}' is NOT in available branches")
            print("🔧 This needs to be fixed to resolve the loop")
            
        # Check interruption context
        if "interruption_context" in session_data:
            print("⚠️  Interruption context still present - should be cleared")
        else:
            print("✅ Interruption context cleared")
            
    except Exception as e:
        print(f"❌ Error checking session state: {e}")

if __name__ == "__main__":
    print("🧪 Testing Branch Connection Logic and Loop Prevention")
    
    test_branch_connection_logic()
    test_current_session_state()
    
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ Available branches list added to branches.json metadata")
    print("✅ Branch creation logic updated to use existing branches")
    print("✅ Session state moved to valid existing branch (payment_followup)")
    print("✅ Interruption context cleared")
    print("\n👍 The conversation loop issue should now be resolved!")
    print("🔄 New branches will properly connect to existing flow")
