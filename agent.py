import json
import re
import os
from dotenv import load_dotenv
from prompt_builder import build_prompt, render_template
from gemini_api import send_to_gemini
from branches_manager import BranchesManager
from interruption_handler import InterruptionHandler

# Load environment variables from .env file
load_dotenv()

# Get API key - hardcoded for reliability
api_key = "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM"

# Initialize Branches Manager
branches_manager = BranchesManager("branches.json", "suggestions.json")

# Initialize Interruption Handler
interruption_handler = InterruptionHandler(branches_manager)

# Load static user data
with open('user_data.json', 'r', encoding='utf-8') as f:
    user_data = json.load(f)

# Load or initialize session data
try:
    with open('session_data.json', 'r', encoding='utf-8') as f:
        session_data = json.load(f)
except FileNotFoundError:
    session_data = {
        "conversation_stage": "greeting",
        "language_preference": "English",
        "user_agreed_to_pay": None,
        "callback_scheduled": False,
        "chat_history": [],
        "last_intent": None
    }

# ✅ FIX: Corrected to WRITE session_data
def save_session():
    with open('session_data.json', 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=4)

def extract_metadata(response):
    try:
        match = re.search(r'```json\n({.*?})\n```', response, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print("JSON extraction error:", e)
    return {}

def check_if_response_matches_expected(user_input, current_stage):
    """
    Check if user input matches any expected response pattern for the current stage.
    Returns (matches, matched_response_type, scripted_response, next_stage)
    """
    current_branch = branches_manager.read_branch(current_stage)
    if not current_branch:
        return False, None, None, None
    
    expected_responses = current_branch.get("expected_user_responses", {})
    if not expected_responses:
        return False, None, None, None
    
    user_input_lower = user_input.lower() if user_input else ""
    
    print(f"🔍 DEBUG: Looking for matches in expected responses: {list(expected_responses.keys())}")
    
    # STEP 1: Check direct keyword matches from branches.json
    for response_type, response_data in expected_responses.items():
        keywords = response_data.get("keywords", [])
        if keywords:
            print(f"🔍 DEBUG: Checking {response_type} with keywords: {keywords}")
            # Check if any keyword matches the user input
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    # Check for negations before confirming match
                    negation_patterns = [
                        f"no {keyword.lower()}",
                        f"don't {keyword.lower()}",
                        f"dont {keyword.lower()}",
                        f"not {keyword.lower()}",
                        f"no i don't {keyword.lower()}",
                        f"no i dont {keyword.lower()}",
                        f"i don't {keyword.lower()}",
                        f"i dont {keyword.lower()}",
                        f"i don't have {keyword.lower()}",
                        f"i dont have {keyword.lower()}",
                        f"no i don't have {keyword.lower()}",
                        f"no i dont have {keyword.lower()}"
                    ]
                    
                    # If user is negating the keyword, skip this match
                    if any(neg_pattern in user_input_lower for neg_pattern in negation_patterns):
                        print(f"❌ NEGATION DETECTED: '{keyword}' found but negated in '{user_input}'")
                        continue
                    
                    print(f"✅ KEYWORD MATCH: '{keyword}' found in '{user_input}'")
                    return True, response_type, response_data.get("response"), response_data.get("next")
    
    # STEP 2: Fallback to generic patterns for responses without keywords
    generic_patterns = {
        "yes": ["yes", "ok", "okay", "fine", "sure", "correct", "right", "speaking", "this is", "i am", "yeah", "yep", "alright", "absolutely", "go ahead", "proceed", "continue", "right time"],
        "no": ["no", "not", "nope", "wrong", "incorrect", "not me", "not here", "not available", "not now", "later", "busy", "not good time", "call back"],
    }
    
    print(f"🔍 DEBUG: No keyword matches found, checking generic patterns")
    
    # STEP 2.5: Special case handling for negated responses
    # "no questions" or "don't have questions" in policy_status_explanation should be treated as "wants_to_proceed"
    if current_stage == "policy_status_explanation":
        no_questions_patterns = [
            "no questions", "dont have questions", "don't have questions", 
            "no i dont have questions", "no i don't have questions",
            "i dont have questions", "i don't have questions"
        ]
        if any(pattern in user_input_lower for pattern in no_questions_patterns):
            print(f"🎯 SPECIAL CASE: 'no questions' in policy_status_explanation treated as 'wants_to_proceed'")
            if "wants_to_proceed" in expected_responses:
                return True, "wants_to_proceed", expected_responses["wants_to_proceed"].get("response"), expected_responses["wants_to_proceed"].get("next")
    
    # STEP 3: Fallback to generic patterns for responses without keywords
    for response_type, response_data in expected_responses.items():
        # Only use generic patterns if no keywords are defined
        if not response_data.get("keywords"):
            if response_type in generic_patterns:
                print(f"🔍 DEBUG: Checking generic pattern {response_type}: {generic_patterns[response_type]}")
                if any(pattern in user_input_lower for pattern in generic_patterns[response_type]):
                    print(f"✅ GENERIC MATCH: '{response_type}' pattern matched")
                    return True, response_type, response_data.get("response"), response_data.get("next")
    
    return False, None, None, None

def find_appropriate_existing_branch(user_input, current_stage):
    """
    Try to find an existing branch that could handle this unexpected response.
    Returns (branch_name, confidence_score) or (None, 0) if no good match found.
    """
    user_input_lower = user_input.lower() if user_input else ""
    
    # STEP 1: Handle generic affirmative responses based on context
    generic_affirmatives = ["sure", "okay", "alright", "fine", "proceed", "continue", "go ahead"]
    if any(word in user_input_lower for word in generic_affirmatives):
        context_mappings = {
            "policy_status_explanation": ("wants_to_know_importance", 0.8, "User agrees to hear more explanation"),
            "explain_policy_loss": ("wants_payment_options", 0.8, "After explanation, user typically wants payment options"),
            "payment_followup": ("online", 0.7, "Generic agreement in payment context usually means online payment"),
            "policy_confirmation": ("confirms_basic_details", 0.8, "Generic agreement to policy details"),
            "general_help": ("policy_benefits", 0.7, "Generic agreement to help usually means wanting to know benefits"),
            "rebuttals": ("wants_payment_options", 0.7, "After rebuttals, user agreeing usually means ready to pay")
        }
        
        if current_stage in context_mappings:
            target_branch, confidence, reasoning = context_mappings[current_stage]
            # Check if the target branch actually exists in the current stage's expected responses
            current_branch = branches_manager.read_branch(current_stage)
            if current_branch and target_branch in current_branch.get("expected_user_responses", {}):
                print(f"🎯 Context-aware mapping: '{user_input}' in {current_stage} → {target_branch}")
                print(f"💡 Reasoning: {reasoning}")
                return target_branch, confidence
    
    # STEP 2: Handle generic negative responses
    generic_negatives = ["nah", "nope", "not really", "not now", "maybe not"]
    if any(word in user_input_lower for word in generic_negatives):
        # These typically map to 'no' responses or scheduling
        return "reschedule", 0.6
    
    # STEP 3: Standard keyword-based mapping
    branch_mappings = {
        # Payment related responses
        "payment_followup": ["pay", "payment", "how to pay", "money", "card", "online", "upi", "cheque", "cost", "amount"],
        "payment_inquiry": ["can't pay", "financial problem", "difficult", "expensive", "broke", "budget", "tight"],
        "payment_already_made": ["already paid", "paid", "done", "completed", "cleared", "settled"],
        
        # Policy information requests
        "policy_confirmation": ["policy details", "what policy", "my policy", "benefits", "coverage", "details"],
        "explain_policy_loss": ["what happens", "benefits", "importance", "why", "explain", "understand"],
        
        # Financial concerns and objections
        "financial_problem_handling": ["money problem", "financial", "afford", "crisis", "expensive"],
        "rebuttals": ["not interested", "don't want", "refuse", "won't pay", "cancel"],
        
        # Scheduling and timing
        "reschedule": ["later", "callback", "call back", "busy", "not good time", "different time"],
        "schedule_callback": ["tomorrow", "next week", "evening", "morning", "weekend"],
        
        # Alternative scenarios
        "scenario_market_high": ["market", "volatile", "risky", "unstable"],
        "scenario_emergency_needs": ["emergency", "medical", "urgent", "hospital"],
        "scenario_better_alternatives": ["mutual fund", "fd", "better option", "alternative"],
        "scenario_low_returns": ["poor returns", "low returns", "loss", "not profitable"],
        
        # Help and clarification
        "general_help": ["help", "confused", "don't understand", "explain", "clarify"],
        "policy_bond_help": ["policy document", "bond", "papers", "certificate"],
        
        # Default fallbacks
        "default_fallback": ["unclear", "other", "different"],
        "unexpected_response_handler": ["specific concern", "elaborate", "discuss"]
    }
    
    best_match = None
    highest_score = 0
    
    for branch_name, keywords in branch_mappings.items():
        # Skip current stage to avoid loops
        if branch_name == current_stage:
            continue
            
        # Check if branch exists
        if not branches_manager.read_branch(branch_name):
            continue
            
        # Calculate match score
        matches = sum(1 for keyword in keywords if keyword in user_input_lower)
        if matches > 0:
            # Score based on keyword matches and keyword specificity
            score = matches / len(keywords)
            if score > highest_score:
                highest_score = score
                best_match = branch_name
    
    # Only return match if confidence is reasonable
    if highest_score >= 0.1:  # At least 10% keyword match
        return best_match, highest_score
    
    return None, 0

def analyze_user_response_and_suggest(user_input, current_stage, user_data, session_data):
    """
    Analyze unexpected user response. First try to redirect to existing branch,
    only create new branch suggestion if no suitable existing branch found.
    Returns (bot_response, metadata, is_unexpected)
    """
    # STEP 0: Check if we just returned from an interruption - be more lenient with branch creation
    recently_returned_from_interruption = session_data.get("returned_from_interruption", False)
    if recently_returned_from_interruption:
        print("🔄 Recently returned from interruption - providing gentle redirect instead of creating branch")
        # Clear the flag
        session_data["returned_from_interruption"] = False
        return "I understand. Let's continue with your policy details.", {
            "intent": "gentle_redirect",
            "update": {
                "conversation_stage": current_stage,
                "language_preference": session_data.get('language_preference', 'English')
            }
        }, False
    
    # STEP 1: Try to find existing branch that could handle this response
    existing_branch, confidence = find_appropriate_existing_branch(user_input, current_stage)
    
    if existing_branch and confidence > 0.2:  # Good confidence match
        print(f"🔄 Redirecting to existing branch: {existing_branch} (confidence: {confidence:.2f})")
        
        # Get the existing branch data
        branch_data = branches_manager.read_branch(existing_branch)
        if branch_data:
            # Use Gemini to create a smooth transition to the existing branch
            transition_prompt = f"""
You are Veena, an experienced insurance agent from ValuEnable Life Insurance. The user gave an unexpected response, but I found an existing conversation branch that can handle their concern.

CONTEXT:
- Current stage: {current_stage}
- User input: "{user_input}" (unexpected response)
- Redirecting to existing branch: {existing_branch}
- Target branch intent: {branch_data.get('intent', 'Unknown')}
- Target branch prompt: {branch_data.get('bot_prompt', '')}
- User data: {json.dumps(user_data, indent=2)}

TASK: Create a smooth transition response that acknowledges the user's input and naturally leads into the target branch conversation.

RESPONSE FORMAT:

[Your natural transition response as Veena that smoothly moves to the target branch topic]

```json
{{
  "intent": "{branch_data.get('intent', 'handle_redirect')}",
  "update": {{
    "conversation_stage": "{existing_branch}",
    "language_preference": "{session_data.get('language_preference', 'English')}"
  }},
  "is_unexpected": true,
  "redirect_to_existing": true,
  "redirected_branch": "{existing_branch}",
  "confidence": {confidence}
}}
```
"""
            
            try:
                gemini_response = send_to_gemini(transition_prompt, api_key)
                metadata = extract_metadata(gemini_response)
                clean_response = gemini_response.strip().split("```json")[0].strip()
                
                print(f"✅ Successfully redirected to existing branch: {existing_branch}")
                return clean_response, metadata, True
                
            except Exception as e:
                print(f"Error in redirect transition: {e}")
                # Fall through to branch creation logic
    
    # STEP 2: No suitable existing branch found, proceed with original logic
    print(f"🆕 No suitable existing branch found (best match: {existing_branch}, confidence: {confidence:.2f})")
    print("📝 Creating new branch suggestion...")
    
    current_branch = branches_manager.read_branch(current_stage)
    expected_responses = current_branch.get("expected_user_responses", {}) if current_branch else {}
    
    # Get available branches list from branches.json
    all_branches = branches_manager.read_all_branches()
    available_branches = all_branches.get("_metadata", {}).get("available_branches", [])
    
    # Get pending suggestions for context
    pending_suggestions = branches_manager.get_pending_suggestions()
    suggestions_context = ""
    if pending_suggestions.get("pending_operations"):
        suggestions_context = f"\n\nCURRENT PENDING SUGGESTIONS (Veena's previous suggestions):\n{json.dumps(pending_suggestions, indent=2)}"
    
    analysis_prompt = f"""
You are Veena, an experienced insurance agent from ValuEnable Life Insurance. The user has given an UNEXPECTED response that doesn't match any expected response patterns and couldn't be redirected to existing branches.

CURRENT CONVERSATION CONTEXT:
- Current stage: {current_stage}
- User input: "{user_input}" (UNEXPECTED RESPONSE)
- Expected responses for this stage: {json.dumps(expected_responses, indent=2)}
- User data: {json.dumps(user_data, indent=2)}
- Session data: {json.dumps(session_data, indent=2)}{suggestions_context}

AVAILABLE BRANCHES (MUST USE FOR next_stage):
{json.dumps(available_branches, indent=2)}

ANALYSIS PERFORMED:
- Checked for existing branches that could handle this response
- Best existing match: {existing_branch or 'None'} (confidence: {confidence:.2f})
- No suitable existing branch found, creating new branch suggestion

CRITICAL INSTRUCTIONS:
1. For "next" values in expected_user_responses, ONLY use branches from the AVAILABLE BRANCHES list above
2. This prevents conversation loops and ensures proper flow
3. Choose the most appropriate existing branch based on the user's likely intent after this response
4. If user seems ready to pay → use "payment_followup" or "payment_details"
5. If user has concerns → use "financial_problem_handling" or "rebuttals"
6. If user wants to reschedule → use "schedule_callback"
7. If unclear → use "policy_confirmation" or "closure"

TASK: Handle this unexpected response and create a branch suggestion.

1. Respond naturally to the user as Veena would handle this unexpected situation
2. Create a branch suggestion to handle similar unexpected responses in the future
3. Choose next stages ONLY from the available branches list above

RESPONSE FORMAT:

[Your natural response as Veena to handle this unexpected situation]

```json
{{
  "intent": "handle_unexpected_response",
  "update": {{
    "conversation_stage": "{current_stage}_handled",
    "language_preference": "{session_data.get('language_preference', 'English')}"
  }},
  "is_unexpected": true,
  "branch_suggestion": {{
    "action": "create",
    "reasoning": "Why this new branch would help handle similar unexpected responses (no existing branch was suitable)",
    "suggestion_details": {{
      "branch_name": "{current_stage}_handled",
      "intent": "handle_unexpected_from_{current_stage}",
      "bot_prompt": "How Veena should respond to similar unexpected cases in the future",
      "expected_user_responses": {{
        "positive": {{
          "next": "most_appropriate_existing_branch_from_available_list",
          "response": "Follow-up response for positive reaction"
        }},
        "negative": {{
          "next": "appropriate_fallback_existing_branch_from_available_list", 
          "response": "Follow-up response for negative reaction"
        }}
      }},
      "called_when": [{{
        "previous_intent": "{current_branch.get('intent', '') if current_branch else ''}",
        "previous_response": "unexpected_response",
        "response_of_previous_response": "{user_input}"
      }}]
    }}
  }}
}}
```
"""

    try:
        gemini_response = send_to_gemini(analysis_prompt, api_key)
        metadata = extract_metadata(gemini_response)
        
        # Process branch suggestion
        if "branch_suggestion" in metadata:
            branch_suggestion = metadata["branch_suggestion"]
            details = branch_suggestion.get("suggestion_details", {})
            
            if details.get("branch_name"):
                success = branches_manager.create_branch(
                    branch_name=details["branch_name"],
                    intent=details.get("intent", "handle_unexpected"),
                    bot_prompt=details.get("bot_prompt", ""),
                    expected_user_responses=details.get("expected_user_responses", {}),
                    called_when=details.get("called_when", [])
                )
                if success:
                    print(f"✨ Veena suggested creating new branch: {details['branch_name']}")
                    print(f"💡 Reasoning: {branch_suggestion.get('reasoning', 'To handle similar responses better')}")
        
        # Return clean response (without JSON)
        clean_response = gemini_response.strip().split("```json")[0].strip()
        return clean_response, metadata, True
        
    except Exception as e:
        print(f"Error in Gemini analysis: {e}")
        return "I understand. Let me help you with this. Can you please clarify what you mean?", {}, True

def process_conversation_turn(user_input, current_stage, user_data, session_data):
    """
    Process a single conversation turn with interruption handling.
    
    Returns:
        Tuple of (bot_response, metadata, conversation_continues)
    """
    # STEP 0: Check if we're in an interruption flow and handle response
    if interruption_handler.is_in_interruption_flow(session_data):
        print(f"🔄 INTERRUPTION FLOW: Handling response to current interruption")
        bot_response, metadata, should_continue = interruption_handler.handle_interruption_response(
            user_input, session_data, user_data
        )
        
        # ✅ IMPROVED: Check if we just resolved an interruption
        if metadata.get("interruption_resolved"):
            restored_stage = metadata.get("restored_to_stage")
            print(f"✅ INTERRUPTION RESOLVED: Restored to stage '{restored_stage}'")
            
            # Update the current_stage for the rest of this function
            current_stage = restored_stage
            session_data["conversation_stage"] = restored_stage
        
        return bot_response, metadata, should_continue
    
    # ✅ IMPROVED: Handle post-interruption responses more gracefully
    if session_data.get("returned_from_interruption", False):
        print(f"🔄 POST-INTERRUPTION: Back at stage '{current_stage}' after interruption")
        
        # First check if this is a valid response for the restored stage
        matches_expected, matched_type, scripted_response, next_stage = check_if_response_matches_expected(
            user_input, current_stage
        )
        
        if matches_expected:
            print(f"✅ POST-INTERRUPTION MATCH: User response fits restored stage")
            # Clear the flag and process normally
            session_data["returned_from_interruption"] = False
            # Continue with normal processing below
        else:
            # Give user another chance to respond appropriately to the restored stage
            print(f"❓ POST-INTERRUPTION: User response doesn't fit restored stage, providing context")
            session_data["returned_from_interruption"] = False
            
            # Get current stage prompt to re-contextualize
            current_branch = branches_manager.read_branch(current_stage)
            if current_branch:
                stage_prompt = current_branch.get("bot_prompt", "")
                if stage_prompt:
                    from prompt_builder import render_template
                    contextualized_prompt = render_template(stage_prompt, user_data)
                    return f"To clarify where we were: {contextualized_prompt}", {
                        "intent": "post_interruption_clarification",
                        "update": {
                            "conversation_stage": current_stage,
                            "language_preference": session_data.get('language_preference', 'English')
                        }
                    }, True
    
    # STEP 1: Check for interruptions first with flexible thresholds
    is_interruption, intent_name, confidence = interruption_handler.detect_interruption(
        user_input, current_stage, confidence_threshold=0.4  # Lower threshold for compound responses
    )
    
    # STEP 1.5: Special handling for compound responses (response + interruption)
    # Check if user input contains common response words + interruption keywords
    user_input_lower = user_input.lower() if user_input else ""
    contains_response_words = any(word in user_input_lower for word in ["yes", "no", "ok", "okay", "sure"])
    contains_question_words = any(word in user_input_lower for word in ["where", "how", "why", "what", "who", "when"])
    
    # If it's a compound response, prioritize interruption if confidence is reasonable
    if contains_response_words and contains_question_words and confidence >= 0.3:
        print(f"🔄 COMPOUND RESPONSE DETECTED: Response words + Question words")
        print(f"🔔 Prioritizing interruption: {intent_name} (confidence: {confidence:.2f})")
        is_interruption = True
    
    if is_interruption:
        print(f"🔔 INTERRUPTION DETECTED: {intent_name} (confidence: {confidence:.2f})")
        
        # Handle the interruption
        bot_response, metadata, should_resume = interruption_handler.handle_interruption(
            intent_name, user_input, current_stage, session_data, user_data
        )
        
        # Check if this is a critical interruption that changes flow completely
        if interruption_handler.is_critical_interruption(intent_name):
            print(f"🚨 Critical interruption: {intent_name}")
            return bot_response, metadata, True
        
        # For non-critical interruptions that should return to main flow
        if should_resume:
            # Get the interruption intent data to check if it should return to main flow
            intent_data = interruption_handler.interruptible_intents.get(intent_name, {})
            if intent_data.get("return_to_main_flow", False):
                # Stay in the same stage and add transition
                print(f"🔄 Returning to main flow at stage: {current_stage}")
                metadata.setdefault("update", {})["conversation_stage"] = current_stage
                metadata["interruption_handled"] = True
                metadata["returned_to_main_flow"] = True
        
        return bot_response, metadata, True
    
    # STEP 2: Normal flow - check if response matches expected patterns
    matches_expected, matched_type, scripted_response, next_stage = check_if_response_matches_expected(
        user_input, current_stage
    )
    
    if matches_expected:
        print(f"🎯 EXPECTED RESPONSE MATCH: Type='{matched_type}', Next='{next_stage}'")
        
        if scripted_response:
            # Use the exact scripted response with user data filled in
            from prompt_builder import render_template
            bot_response = render_template(scripted_response, user_data)
            current_branch_data = branches_manager.read_branch(current_stage)
            metadata = {
                "intent": current_branch_data.get("intent", "unknown") if current_branch_data else "unknown",
                "update": {
                    "conversation_stage": next_stage or current_stage,
                    "language_preference": session_data.get("language_preference", "English")
                }
            }
        else:
            # No scripted response, use prompt builder for this stage
            prompt = build_prompt(user_input, user_data, session_data)
            bot_response = send_to_gemini(prompt, api_key)
            clean_response = bot_response.strip().split("```json")[0].strip()
            bot_response = clean_response
            metadata = extract_metadata(bot_response)
            
            # Override next stage if provided in branch
            if next_stage and "update" in metadata:
                metadata["update"]["conversation_stage"] = next_stage
        
        return bot_response, metadata, True
    
    # STEP 3: Unexpected response - use Gemini analysis
    print("🤖 Using Gemini for unexpected response")
    bot_response, metadata, is_unexpected = analyze_user_response_and_suggest(
        user_input, current_stage, user_data, session_data
    )
    return bot_response, metadata, True
    bot_response, metadata, is_unexpected = analyze_user_response_and_suggest(
        user_input, current_stage, user_data, session_data
    )
    return bot_response, metadata, True

def main():
    """Main function to run the agent conversation"""
    
    # === Initial Greeting by Veena if stage is "greeting" ===
    if session_data.get("conversation_stage") == "greeting":
        prompt = build_prompt("", user_data, session_data)
        bot_response = send_to_gemini(prompt, api_key)
        print(bot_response.strip().split("```json")[0].strip())

        metadata = extract_metadata(bot_response)
        if "update" in metadata:
            for k, v in metadata["update"].items():
                session_data[k] = v
        if "intent" in metadata:
            session_data["last_intent"] = metadata["intent"]

        # ✅ FIX: Safe chat history append
        session_data.setdefault("chat_history", []).append({
            "user": None,
            "veena": bot_response
        })

        save_session()

    # === Main Conversation Loop ===
    while True:
        user_input = input("User says: ")
        
        current_stage = session_data.get("conversation_stage", "greeting")
        
        if user_input.strip():  # Only process if user provided input
            # Debug: Show current state
            print(f"\n🔍 DEBUG: Current stage: {current_stage}")
            current_branch = branches_manager.read_branch(current_stage)
            if current_branch:
                expected_types = list(current_branch.get("expected_user_responses", {}).keys())
                print(f"🔍 DEBUG: Expected response types: {expected_types}")
            
            # Process conversation turn with interruption handling
            bot_response, metadata, conversation_continues = process_conversation_turn(
                user_input, current_stage, user_data, session_data
            )
            
            print(bot_response)
        
        else:
            # Empty input, use normal flow
            prompt = build_prompt(user_input, user_data, session_data)
            bot_response = send_to_gemini(prompt, api_key)
            print(bot_response.strip().split("```json")[0].strip())
            metadata = extract_metadata(bot_response)

        # Update session data based on metadata
        if "update" in metadata:
            for k, v in metadata["update"].items():
                session_data[k] = v
        if "intent" in metadata:
            session_data["last_intent"] = metadata["intent"]

        # ✅ FIX: Safe chat history append
        session_data.setdefault("chat_history", []).append({
            "user": user_input,
            "veena": bot_response if 'bot_response' in locals() else "System response"
        })

        save_session()

        if session_data.get("conversation_stage") == "closure":
            print("✅ Conversation completed.")
            
            # Show pending suggestions summary
            pending_suggestions = branches_manager.get_pending_suggestions()
            pending_ops = pending_suggestions.get("pending_operations", [])
            if pending_ops:
                print(f"\n💡 Veena has made {len(pending_ops)} suggestions to improve future conversations.")
                print("Use 'apply_suggestions.py' to review and apply these suggestions to branches.json")
            break

if __name__ == "__main__":
    main()
