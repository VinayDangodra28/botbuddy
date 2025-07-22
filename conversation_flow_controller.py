"""
Conversation Flow Controller
Handles the main conversation processing logic and flow control
"""
import json
from typing import Dict, Any, Tuple, Optional
from branches_manager import BranchesManager
from interruption_handler import InterruptionHandler
from response_analyzer import ResponseAnalyzer
from gemini_api import send_to_gemini
from prompt_builder import build_prompt, render_template


class ConversationFlowController:
    """Controls the main conversation flow and processing logic"""
    
    def __init__(self, branches_manager: BranchesManager, interruption_handler: InterruptionHandler, 
                 response_analyzer: ResponseAnalyzer, api_key: str):
        self.branches_manager = branches_manager
        self.interruption_handler = interruption_handler
        self.response_analyzer = response_analyzer
        self.api_key = api_key
    
    def analyze_user_response_and_suggest(self, user_input: str, current_stage: str, 
                                        user_data: Dict[str, Any], session_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
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
        existing_branch, confidence = self.response_analyzer.find_appropriate_existing_branch(user_input, current_stage)
        
        if existing_branch and confidence >= 0.2:  # Good confidence match
            print(f"🔄 Redirecting to existing branch: {existing_branch} (confidence: {confidence:.2f})")
            
            # Get the existing branch data
            branch_data = self.branches_manager.read_branch(existing_branch)
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
                    gemini_response = send_to_gemini(transition_prompt, self.api_key)
                    metadata = self.response_analyzer.extract_metadata(gemini_response)
                    clean_response = gemini_response.strip().split("```json")[0].strip()
                    
                    print(f"✅ Successfully redirected to existing branch: {existing_branch}")
                    return clean_response, metadata, True
                    
                except Exception as e:
                    print(f"Error in redirect transition: {e}")
                    # Fall through to branch creation logic
        
        # STEP 2: No suitable existing branch found, proceed with original logic
        print(f"🆕 No suitable existing branch found (best match: {existing_branch}, confidence: {confidence:.2f})")
        print("📝 Creating new branch suggestion...")
        
        current_branch = self.branches_manager.read_branch(current_stage)
        expected_responses = current_branch.get("expected_user_responses", {}) if current_branch else {}
        
        # Get available branches list from branches.json
        all_branches = self.branches_manager.read_all_branches()
        available_branches = all_branches.get("_metadata", {}).get("available_branches", [])
        
        # Get pending suggestions for context
        pending_suggestions = self.branches_manager.get_pending_suggestions()
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
            gemini_response = send_to_gemini(analysis_prompt, self.api_key)
            metadata = self.response_analyzer.extract_metadata(gemini_response)
            
            # Process branch suggestion
            if "branch_suggestion" in metadata:
                branch_suggestion = metadata["branch_suggestion"]
                details = branch_suggestion.get("suggestion_details", {})
                
                if details.get("branch_name"):
                    success = self.branches_manager.create_branch(
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
    
    def _handle_callback_confirmation(self, user_input: str, current_stage: str, session_data: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any], bool]]:
        """Handle confirmation for callbacks"""
        # Only proceed if this is a callback continuation that hasn't been confirmed yet
        if not (session_data.get("is_callback") and session_data.get("callback_continuation") and not session_data.get("callback_confirmed")):
            return None
        
        user_input_lower = user_input.lower()
        affirmative = any(word in user_input_lower for word in ["yes", "yeah", "sure", "ok", "okay", "continue", "proceed"])
        negative = any(word in user_input_lower for word in ["no", "not", "busy", "later", "another time", "reschedule"])
        
        # Update callback confirmation status
        if affirmative:
            # User confirms to continue the callback
            response = "Great! Let's continue where we left off with your policy. "
            
            # Add context about what we were discussing
            if "interrupted_stage" in session_data:
                stage = session_data.get("interrupted_stage", current_stage)
                response += f"We were discussing your policy renewal and the payment options available to you."
            else:
                response += f"Let me help you with your policy renewal."
            
            metadata = {
                "intent": "callback_confirmed",
                "update": {
                    "callback_confirmed": True
                }
            }
            
            return response, metadata, True
            
        elif negative:
            # User wants to reschedule again
            response = "I understand this isn't a good time. When would be a better time to call you back?"
            metadata = {
                "intent": "reschedule_callback",
                "interruption_triggered": True,
                "interruption_active": True,
                "awaiting_response": "callback_time"
            }
            
            return response, metadata, True
            
        else:
            # Unclear response, assume they want to continue but ask for confirmation
            response = "I'd like to continue our previous conversation about your policy. Is that okay with you?"
            metadata = {
                "intent": "callback_confirmation",
                "update": {}
            }
            
            return response, metadata, True

    def process_conversation_turn(self, user_input: str, current_stage: str, user_data: Dict[str, Any], 
                                session_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
        """
        Process a single conversation turn with interruption handling.
        
        Returns:
            Tuple of (bot_response, metadata, conversation_continues)
        """
        # Check for callback confirmation if this is a resumed callback
        if session_data.get("is_callback") and session_data.get("callback_continuation") and not session_data.get("callback_confirmed"):
            callback_response = self._handle_callback_confirmation(user_input, current_stage, session_data)
            if callback_response:
                return callback_response
                
        # STEP 0: Check if we're in an interruption flow and handle response
        if self.interruption_handler.is_in_interruption_flow(session_data):
            print(f"🔄 INTERRUPTION FLOW: Handling response to current interruption")
            bot_response, metadata, should_continue = self.interruption_handler.handle_interruption_response(
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
            matches_expected, matched_type, scripted_response, next_stage = self.response_analyzer.check_if_response_matches_expected(
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
                current_branch = self.branches_manager.read_branch(current_stage)
                if current_branch:
                    stage_prompt = current_branch.get("bot_prompt", "")
                    if stage_prompt:
                        contextualized_prompt = render_template(stage_prompt, user_data)
                        return f"To clarify where we were: {contextualized_prompt}", {
                            "intent": "post_interruption_clarification",
                            "update": {
                                "conversation_stage": current_stage,
                                "language_preference": session_data.get('language_preference', 'English')
                            }
                        }, True
        
        # STEP 1: Check for interruptions first with flexible thresholds
        is_interruption, intent_name, confidence = self.interruption_handler.detect_interruption(
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
            bot_response, metadata, should_resume = self.interruption_handler.handle_interruption(
                intent_name, user_input, current_stage, session_data, user_data
            )
            
            # Check if this is a critical interruption that changes flow completely
            if self.interruption_handler.is_critical_interruption(intent_name):
                print(f"🚨 Critical interruption: {intent_name}")
                return bot_response, metadata, True
            
            # For non-critical interruptions that should return to main flow
            if should_resume:
                # Check if we should use intelligent resume stage selection
                intelligent_resume_stage = self.interruption_handler.get_intelligent_resume_stage(
                    session_data, user_data
                )
                
                # Get the interruption intent data to check if it should return to main flow
                intent_data = self.interruption_handler.interruptible_intents.get(intent_name, {})
                if intent_data.get("return_to_main_flow", False):
                    # Use intelligent stage selection or fall back to original stage
                    resume_stage = intelligent_resume_stage or current_stage
                    
                    print(f"🔄 Returning to main flow at stage: {resume_stage}")
                    print(f"   Original stage: {current_stage}, Intelligent suggestion: {intelligent_resume_stage}")
                    
                    metadata.setdefault("update", {})["conversation_stage"] = resume_stage
                    metadata["interruption_handled"] = True
                    metadata["returned_to_main_flow"] = True
                    metadata["resume_stage_info"] = {
                        "original": current_stage,
                        "intelligent": intelligent_resume_stage,
                        "selected": resume_stage
                    }
                    
                    # If we advanced stages, also set flag for smoother handling
                    if resume_stage != current_stage:
                        session_data["returned_from_interruption"] = True
                        session_data["stage_advanced_by_interruption"] = True
            
            return bot_response, metadata, True
        
        # STEP 2: Normal flow - check if response matches expected patterns
        matches_expected, matched_type, scripted_response, next_stage = self.response_analyzer.check_if_response_matches_expected(
            user_input, current_stage
        )
        
        if matches_expected:
            print(f"🎯 EXPECTED RESPONSE MATCH: Type='{matched_type}', Next='{next_stage}'")
            
            if scripted_response:
                # Use the exact scripted response with user data filled in
                bot_response = render_template(scripted_response, user_data)
                current_branch_data = self.branches_manager.read_branch(current_stage)
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
                bot_response = send_to_gemini(prompt, self.api_key)
                clean_response = bot_response.strip().split("```json")[0].strip()
                bot_response = clean_response
                metadata = self.response_analyzer.extract_metadata(bot_response)
                
                # Override next stage if provided in branch
                if next_stage and "update" in metadata:
                    metadata["update"]["conversation_stage"] = next_stage
            
            return bot_response, metadata, True
        
        # STEP 3: Unexpected response - use Gemini analysis
        print("🤖 Using Gemini for unexpected response")
        bot_response, metadata, is_unexpected = self.analyze_user_response_and_suggest(
            user_input, current_stage, user_data, session_data
        )
        return bot_response, metadata, True
