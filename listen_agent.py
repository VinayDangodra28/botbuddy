from eleven_websocket import convert_single_text, play_audio_async
from dotenv import load_dotenv
from prompt_builder import build_prompt, render_template
from gemini_api import send_to_gemini
from branches_manager import BranchesManager
from interruption_handler import InterruptionHandler
import os
import json
import re
import asyncio
import speech_recognition as sr

class VoiceAgent:
    def __init__(self, api_key=None):
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key - use provided key or hardcoded fallback
        self.api_key = api_key or "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM"
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150  # Adjust as needed

        # Initialize Branches Manager
        self.branches_manager = BranchesManager("branches.json", "suggestions.json")
        
        # Initialize Interruption Handler
        self.interruption_handler = InterruptionHandler(self.branches_manager)
        
        # Load static user data
        with open('user_data.json', 'r', encoding='utf-8') as f:
            self.user_data = json.load(f)
        
        # Load or initialize session data
        try:
            with open('session_data.json', 'r', encoding='utf-8') as f:
                self.session_data = json.load(f)
        except FileNotFoundError:
            self.session_data = {
                "conversation_stage": "greeting",
                "language_preference": "English",
                "user_agreed_to_pay": None,
                "callback_scheduled": False,
                "chat_history": [],
                "last_intent": None
            }
    
    def save_session(self):
        """Save current session data to file"""
        with open('session_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=4)
    
    def extract_metadata(self, response):
        """Extract JSON metadata from bot response"""
        try:
            match = re.search(r'```json\n({.*?})\n```', response, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception as e:
            print("JSON extraction error:", e)
        return {}

    def check_if_response_matches_expected(self, user_input, current_stage):
        """
        Check if user input matches any expected response pattern for the current stage.
        Returns (matches, matched_response_type, scripted_response, next_stage)
        """
        current_branch = self.branches_manager.read_branch(current_stage)
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
        
        # STEP 2: Special case handling for negated responses
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
        generic_patterns = {
            "yes": ["yes", "ok", "okay", "fine", "sure", "correct", "right", "speaking", "this is", "i am", "yeah", "yep", "alright", "absolutely", "go ahead", "proceed", "continue", "right time"],
            "no": ["no", "not", "nope", "wrong", "incorrect", "not me", "not here", "not available", "not now", "later", "busy", "not good time", "call back"],
        }
        
        print(f"🔍 DEBUG: No keyword matches found, checking generic patterns")
        
        for response_type, response_data in expected_responses.items():
            # Only use generic patterns if no keywords are defined
            if not response_data.get("keywords"):
                if response_type in generic_patterns:
                    print(f"🔍 DEBUG: Checking generic pattern {response_type}: {generic_patterns[response_type]}")
                    if any(pattern in user_input_lower for pattern in generic_patterns[response_type]):
                        print(f"✅ GENERIC MATCH: '{response_type}' pattern matched")
                        return True, response_type, response_data.get("response"), response_data.get("next")
        
        return False, None, None, None

    def find_appropriate_existing_branch(self, user_input, current_stage):
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
                current_branch = self.branches_manager.read_branch(current_stage)
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
            if not self.branches_manager.read_branch(branch_name):
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

    def analyze_user_response_and_suggest(self, user_input, current_stage, user_data, session_data):
        """
        Analyze unexpected user response. First try to redirect to existing branch,
        only create new branch suggestion if no suitable existing branch found.
        Returns (bot_response, metadata, is_unexpected)
        """
        # STEP 1: Try to find existing branch that could handle this response
        existing_branch, confidence = self.find_appropriate_existing_branch(user_input, current_stage)
        
        if existing_branch and confidence > 0.2:  # Good confidence match
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
                    metadata = self.extract_metadata(gemini_response)
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

    ANALYSIS PERFORMED:
    - Checked for existing branches that could handle this response
    - Best existing match: {existing_branch or 'None'} (confidence: {confidence:.2f})
    - No suitable existing branch found, creating new branch suggestion

    TASK: Handle this unexpected response and create a branch suggestion.

    1. Respond naturally to the user as Veena would handle this unexpected situation
    2. Create a branch suggestion to handle similar unexpected responses in the future
    3. Determine appropriate next stage based on the response

    RESPONSE FORMAT:

    [Your natural response as Veena to handle this unexpected situation]

    ```json
    {{
      "intent": "handle_unexpected_response",
      "update": {{
        "conversation_stage": "appropriate_next_stage_based_on_response",
        "language_preference": "{session_data.get('language_preference', 'English')}"
      }},
      "is_unexpected": true,
      "branch_suggestion": {{
        "action": "create",
        "reasoning": "Why this new branch would help handle similar unexpected responses (no existing branch was suitable)",
        "suggestion_details": {{
          "branch_name": "handle_{current_stage}_unexpected_response",
          "intent": "handle_unexpected_from_{current_stage}",
          "bot_prompt": "How Veena should respond to similar unexpected cases in the future",
          "expected_user_responses": {{
            "positive": {{
              "next": "appropriate_next_stage",
              "response": "Follow-up response for positive reaction"
            }},
            "negative": {{
              "next": "appropriate_fallback_stage", 
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
            metadata = self.extract_metadata(gemini_response)
            
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

    async def text_to_speech(self, text):
        """Convert text to speech using ElevenLabs"""
        try:
            audio_data = await convert_single_text(text)
            if audio_data:
                await play_audio_async(audio_data)
        except Exception as e:
            print(f"TTS Error: {e}")

    async def speech_to_text(self):
        """Convert speech to text using speech recognition"""
        try:
            with sr.Microphone() as source:
                print("\n🎤 Listening... (speak now)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=8)
                
            print("🔄 Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"👤 You said: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("⏰ No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None

    async def process_conversation_turn(self, user_input=None):
        """Process a single conversation turn with interruption handling"""
        
        current_stage = self.session_data.get("conversation_stage", "greeting")
        
        if user_input and user_input.strip():  # Only process if user provided input
            # Debug: Show current state
            print(f"\n🔍 DEBUG: Current stage: {current_stage}")
            current_branch = self.branches_manager.read_branch(current_stage)
            if current_branch:
                expected_types = list(current_branch.get("expected_user_responses", {}).keys())
                print(f"🔍 DEBUG: Expected response types: {expected_types}")
            
            # STEP 1: Check for interruptions first
            is_interruption, intent_name, confidence = self.interruption_handler.detect_interruption(
                user_input, current_stage, confidence_threshold=0.6
            )
            
            if is_interruption:
                print(f"🔔 INTERRUPTION DETECTED: {intent_name} (confidence: {confidence:.2f})")
                
                # Handle the interruption
                bot_response, metadata, should_resume = self.interruption_handler.handle_interruption(
                    intent_name, user_input, current_stage, self.session_data, self.user_data
                )
                
                # Check if this is a critical interruption that changes flow completely
                if self.interruption_handler.is_critical_interruption(intent_name):
                    print(f"� Critical interruption: {intent_name}")
                else:
                    # For non-critical interruptions, handle and potentially resume
                    if should_resume and not self.interruption_handler.is_critical_interruption(intent_name):
                        # Add transition back to main flow
                        resume_stage = self.interruption_handler.get_resume_stage(self.session_data)
                        if resume_stage and resume_stage != current_stage:
                            bot_response += f" Now, let's continue with your policy renewal."
                            metadata.setdefault("update", {})["conversation_stage"] = resume_stage
                            self.interruption_handler.clear_interruption_context(self.session_data)
            
            else:
                # STEP 2: Normal flow - check if response matches expected patterns
                matches_expected, matched_type, scripted_response, next_stage = self.check_if_response_matches_expected(user_input, current_stage)
                
                print(f"🔍 DEBUG: User input '{user_input}' matches expected: {matches_expected}")
                if matches_expected:
                    print(f"🎯 MATCH: Type='{matched_type}', Next='{next_stage}'")
                
                if matches_expected:
                    # Use scripted response and update stage
                    if scripted_response:
                        bot_response = render_template(scripted_response, self.user_data)
                        current_branch_data = self.branches_manager.read_branch(current_stage)
                        metadata = {
                            "intent": current_branch_data.get("intent", "unknown") if current_branch_data else "unknown",
                            "update": {
                                "conversation_stage": next_stage or current_stage,
                                "language_preference": self.session_data.get("language_preference", "English")
                            }
                        }
                    else:
                        # No scripted response, use prompt builder for this stage
                        prompt = build_prompt(user_input, self.user_data, self.session_data)
                        bot_response = send_to_gemini(prompt, self.api_key)
                        clean_response = bot_response.strip().split("```json")[0].strip()
                        bot_response = clean_response
                        metadata = self.extract_metadata(bot_response)
                        
                        # Override next stage if provided in branch
                        if next_stage and "update" in metadata:
                            metadata["update"]["conversation_stage"] = next_stage
                
                else:
                    # Use Gemini for unexpected responses
                    print("� Using Gemini for unexpected response")
                    bot_response, metadata, is_unexpected = self.analyze_user_response_and_suggest(user_input, current_stage, self.user_data, self.session_data)
        
        else:
            # Empty input, use normal flow
            prompt = build_prompt("", self.user_data, self.session_data)
            bot_response = send_to_gemini(prompt, self.api_key)
            clean_response = bot_response.strip().split("```json")[0].strip()
            print(clean_response)
            bot_response = clean_response
            metadata = self.extract_metadata(bot_response)
        # Update session data based on metadata
        if "update" in metadata:
            for k, v in metadata["update"].items():
                self.session_data[k] = v
        if "intent" in metadata:
            self.session_data["last_intent"] = metadata["intent"]

        # Safe chat history append
        self.session_data.setdefault("chat_history", []).append({
            "user": user_input,
            "veena": bot_response if 'bot_response' in locals() else "System response"
        })

        self.save_session()

        # Convert to speech
        if 'bot_response' in locals() and bot_response:
            await self.text_to_speech(bot_response)
        
        return self.session_data.get("conversation_stage") != "closure"

    async def run_voice_conversation(self):
        """Main voice conversation loop"""
        print("🤖 Voice Agent Started!")
        print("💡 Tip: Speak clearly after the listening prompt")
        
        # Initial greeting if stage is "greeting"
        if self.session_data.get("conversation_stage") == "greeting":
            prompt = build_prompt("", self.user_data, self.session_data)
            bot_response = send_to_gemini(prompt, self.api_key)
            clean_response = bot_response.strip().split("```json")[0].strip()
            print(f"🤖 Veena: {clean_response}")
            
            metadata = self.extract_metadata(bot_response)
            if "update" in metadata:
                for k, v in metadata["update"].items():
                    self.session_data[k] = v
            if "intent" in metadata:
                self.session_data["last_intent"] = metadata["intent"]

            # Safe chat history append
            self.session_data.setdefault("chat_history", []).append({
                "user": None,
                "veena": clean_response
            })

            self.save_session()
            await self.text_to_speech(clean_response)

        # Main conversation loop
        while True:
            user_input = await self.speech_to_text()
            
            if user_input:
                continue_conversation = await self.process_conversation_turn(user_input)
                if not continue_conversation:
                    print("✅ Conversation completed.")
                    
                    # Show pending suggestions summary
                    pending_suggestions = self.branches_manager.get_pending_suggestions()
                    pending_ops = pending_suggestions.get("pending_operations", [])
                    if pending_ops:
                        print(f"\n💡 Veena has made {len(pending_ops)} suggestions to improve future conversations.")
                        print("Use 'apply_suggestions.py' to review and apply these suggestions to branches.json")
                    break
            else:
                print("❓ No input received. Try speaking again or press Ctrl+C to exit.")

    def process_conversation_turn_with_interruptions(self, user_input=None):
        """Process a single conversation turn with interruption handling for voice agent"""
        
        current_stage = self.session_data.get("conversation_stage", "greeting")
        
        if user_input and user_input.strip():  # Only process if user provided input
            # Debug: Show current state
            print(f"\n🔍 DEBUG: Current stage: {current_stage}")
            current_branch = self.branches_manager.read_branch(current_stage)
            if current_branch:
                expected_types = list(current_branch.get("expected_user_responses", {}).keys())
                print(f"🔍 DEBUG: Expected response types: {expected_types}")
            
            # STEP 1: Check for interruptions first
            is_interruption, intent_name, confidence = self.interruption_handler.detect_interruption(
                user_input, current_stage, confidence_threshold=0.6
            )
            
            if is_interruption:
                print(f"🔔 INTERRUPTION DETECTED: {intent_name} (confidence: {confidence:.2f})")
                
                # Handle the interruption
                bot_response, metadata, should_resume = self.interruption_handler.handle_interruption(
                    intent_name, user_input, current_stage, self.session_data, self.user_data
                )
                
                # Check if this is a critical interruption that changes flow completely
                if self.interruption_handler.is_critical_interruption(intent_name):
                    print(f"🚨 Critical interruption: {intent_name}")
                    return bot_response, metadata
                
                # For non-critical interruptions, handle and potentially resume
                if should_resume and not self.interruption_handler.is_critical_interruption(intent_name):
                    # Add transition back to main flow
                    resume_stage = self.interruption_handler.get_resume_stage(self.session_data)
                    if resume_stage and resume_stage != current_stage:
                        bot_response += f" Now, let's continue with your policy renewal."
                        metadata.setdefault("update", {})["conversation_stage"] = resume_stage
                        self.interruption_handler.clear_interruption_context(self.session_data)
                
                return bot_response, metadata
            
            # STEP 2: Normal flow - check if response matches expected patterns
            matches_expected, matched_type, scripted_response, next_stage = self.check_if_response_matches_expected(user_input, current_stage)
            
            print(f"🔍 DEBUG: User input '{user_input}' matches expected: {matches_expected}")
            if matches_expected:
                print(f"🎯 MATCH: Type='{matched_type}', Next='{next_stage}'")
            
            if matches_expected:
                # Use scripted response and update stage
                bot_response = scripted_response
                current_branch_data = self.branches_manager.read_branch(current_stage)
                metadata = {
                    "intent": current_branch_data.get("intent", "unknown") if current_branch_data else "unknown",
                    "update": {"conversation_stage": next_stage or current_stage}
                }
                return bot_response, metadata
            
            else:
                # Use Gemini for unexpected responses
                print("🤖 Using Gemini for unexpected response")
                bot_response, metadata, is_unexpected = self.analyze_user_response_and_suggest(user_input, current_stage, self.user_data, self.session_data)
                return bot_response, metadata
        
        else:
            # Empty input, use normal flow
            prompt = build_prompt("", self.user_data, self.session_data)
            bot_response = send_to_gemini(prompt, self.api_key)
            clean_response = bot_response.strip().split("```json")[0].strip()
            metadata = self.extract_metadata(bot_response)
            return clean_response, metadata

async def main():
    """Main function to run the voice agent"""
    try:
        # Use hardcoded API key for reliability
        api_key = "AIzaSyCVmLsJE63bOtoUb2dHcskHdWbkCAsebdM"
        
        # Create and run voice agent
        agent = VoiceAgent(api_key)
        await agent.run_voice_conversation()
        
    except KeyboardInterrupt:
        print("\n👋 Voice conversation ended by user.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
