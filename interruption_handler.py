import json
import re
from typing import Dict, List, Tuple, Optional, Any


class InterruptionHandler:
    """
    Handles interruptions in the insurance conversation flow.
    Manages context switching, resumption, and interruption detection.
    """
    
    def __init__(self, branches_manager):
        """
        Initialize interruption handler with branches manager.
        
        Args:
            branches_manager: BranchesManager instance for accessing conversation data
        """
        self.branches_manager = branches_manager
        self.interruptible_intents = self._load_interruptible_intents()
        
    def _load_interruptible_intents(self) -> Dict[str, Any]:
        """Load interruptible intents from branches.json"""
        branches = self.branches_manager.read_all_branches()
        return branches.get("interruptible_intents", {})
    
    def detect_interruption(self, user_input: str, current_stage: str, confidence_threshold: float = 0.6) -> Tuple[bool, Optional[str], float]:
        """
        Detect if user input is an interruption intent.
        
        Args:
            user_input: User's input text
            current_stage: Current conversation stage
            confidence_threshold: Minimum confidence to consider as interruption
            
        Returns:
            Tuple of (is_interruption, intent_name, confidence_score)
        """
        if not user_input or not self.interruptible_intents:
            return False, None, 0.0
            
        user_input_lower = user_input.lower().strip()
        best_match = None
        highest_confidence = 0.0
        
        for intent_name, intent_data in self.interruptible_intents.items():
            # Check if this intent can interrupt the current stage
            interruptible_stages = intent_data.get("interruptible_stages", [])
            if interruptible_stages != ["*"] and current_stage not in interruptible_stages:
                continue
                
            keywords = intent_data.get("keywords", [])
            confidence = self._calculate_keyword_confidence(user_input_lower, keywords)
            
            # Apply priority weighting
            priority_weight = self._get_priority_weight(intent_data.get("priority", "medium"))
            weighted_confidence = confidence * priority_weight
            
            if weighted_confidence > highest_confidence:
                highest_confidence = weighted_confidence
                best_match = intent_name
        
        is_interruption = highest_confidence >= confidence_threshold
        return is_interruption, best_match, highest_confidence
    
    def _calculate_keyword_confidence(self, user_input: str, keywords: List[str]) -> float:
        """Calculate confidence score based on keyword matches"""
        if not keywords:
            return 0.0
            
        total_keywords = len(keywords)
        matched_keywords = 0
        best_match_score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in user_input:
                matched_keywords += 1
                # Calculate match quality - longer matches are better
                match_score = len(keyword_lower) / len(user_input) if len(user_input) > 0 else 0
                best_match_score = max(best_match_score, match_score)
                
        if matched_keywords == 0:
            return 0.0
            
        # Base confidence from keyword matching
        base_confidence = matched_keywords / total_keywords
        
        # Boost confidence for high-quality matches
        if best_match_score > 0.3:  # If the matched keyword covers >30% of user input
            base_confidence = min(1.0, base_confidence + 0.4)
        elif best_match_score > 0.15:  # If the matched keyword covers >15% of user input  
            base_confidence = min(1.0, base_confidence + 0.2)
            
        # Special boost for exact phrase matches
        for keyword in keywords:
            if keyword.lower() == user_input.strip():
                base_confidence = min(1.0, base_confidence + 0.3)
                break
                
        # Even if only one keyword matches, give minimum confidence if it's a good match
        if matched_keywords >= 1 and best_match_score > 0.1:
            base_confidence = max(base_confidence, 0.5)
                
        return base_confidence
    
    def _get_priority_weight(self, priority: str) -> float:
        """Get priority weight multiplier"""
        priority_weights = {
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }
        return priority_weights.get(priority, 1.0)
    
    def handle_interruption(self, intent_name: str, user_input: str, current_stage: str, 
                          session_data: Dict, user_data: Dict) -> Tuple[str, Dict, bool]:
        """
        Enhanced interruption handling with proper stage preservation.
        
        Args:
            intent_name: Name of the interruption intent
            user_input: User's input text
            current_stage: Current conversation stage
            session_data: Current session data
            user_data: User profile data
            
        Returns:
            Tuple of (response_text, updated_metadata, should_resume_main_flow)
        """
        if intent_name not in self.interruptible_intents:
            return "I understand. Let me help you with that.", {}, True
            
        intent_data = self.interruptible_intents[intent_name]
        action = intent_data.get("action", "acknowledge_and_redirect")
        response_template = intent_data.get("response", "I understand.")
        
        # ✅ CRITICAL: Store the CURRENT stage as original_stage for restoration
        session_data["current_interruption"] = {
            "intent_name": intent_name,
            "original_stage": current_stage,  # THIS is where we'll return to
            "user_input": user_input,
            "timestamp": len(session_data.get("chat_history", []))
        }
        
        # Set interruption context
        session_data["interruption_context"] = {
            "in_interruption": True,
            "interruption_type": intent_name,
            "interrupted_stage": current_stage,
            "stage_history": session_data.get("stage_history", []) + [current_stage]  # Track stage progression
        }
        
        # Save current state for resumption if needed
        if intent_data.get("return_to_main_flow", False):
            self._save_interruption_context(session_data, current_stage, intent_name)
        
        # Handle different interruption actions with improved flow control
        if action == "repeat_last_response":
            return self._handle_repeat_request(session_data), {
                "intent": "repeat_request",
                "interruption_triggered": True,
                "original_stage": current_stage,
                "resume_to_stage": current_stage  # Stay at same stage after repeat
            }, True
            
        elif action == "schedule_callback":
            # For schedule_callback, we want to stay in the interruption flow 
            # to handle the user's response about when they want to be called back
            response = self._handle_callback_request(response_template, session_data)
            
            # Keep the interruption active so we can handle the follow-up response
            # DON'T change the conversation stage - keep current_interruption for follow-up handling
            session_data["awaiting_callback_time"] = True
            
            return response, {
                "interruption_triggered": True,
                "interruption_active": True,  # Keep interruption active for follow-up
                "intent": intent_name,
                "awaiting_response": "callback_time"
            }, False  # Don't resume main flow yet, wait for time specification
            
        elif action == "jump_to_payment_flow":
            target_stage = intent_data.get("target_stage", "payment_followup")
            # Clear interruption since we're jumping to a different flow
            session_data.pop("current_interruption", None)
            session_data.pop("interruption_context", None)
            return response_template, {
                "update": {"conversation_stage": target_stage},
                "intent": "early_payment_decision",
                "interruption_handled": True,
                "flow_jump": {"from": current_stage, "to": target_stage}
            }, False
            
        elif action == "jump_to_verification":
            target_stage = intent_data.get("target_stage", "payment_already_made")
            # Clear interruption since we're jumping to a different flow
            session_data.pop("current_interruption", None)
            session_data.pop("interruption_context", None)
            return response_template, {
                "update": {"conversation_stage": target_stage},
                "intent": "payment_verification",
                "interruption_handled": True,
                "flow_jump": {"from": current_stage, "to": target_stage}
            }, False
            
        elif action == "switch_language":
            return self._handle_language_switch(user_input, response_template, session_data), {
                "interruption_handled": True,
                "original_stage": current_stage,
                "resume_to_stage": current_stage,  # Resume at same stage after language switch
                "language_switched": True
            }, True
            
        elif action == "escalate_to_complaint_handling":
            # Clear interruption since we're escalating
            session_data.pop("current_interruption", None)
            session_data.pop("interruption_context", None)
            return response_template, {
                "update": {"conversation_stage": "complaint_handling", "escalation_required": True},
                "interruption_handled": True
            }, False
            
        elif action == "note_supervisor_request":
            session_data["supervisor_requested"] = True
            return response_template, {
                "interruption_handled": True,
                "original_stage": current_stage
            }, True
            
        else:  # Default: acknowledge_and_redirect
            return response_template, {
                "interruption_handled": True,
                "interruption_triggered": True,
                "original_stage": current_stage
            }, True
    
    def _save_interruption_context(self, session_data: Dict, current_stage: str, intent_name: str):
        """Save context for resuming main flow after interruption"""
        session_data["interruption_context"] = {
            "interrupted_stage": current_stage,
            "interruption_intent": intent_name,
            "timestamp": str(json.loads(json.dumps({}, default=str)))
        }
    
    def _handle_repeat_request(self, session_data: Dict) -> str:
        """Handle request to repeat last response"""
        chat_history = session_data.get("chat_history", [])
        if chat_history:
            last_veena_response = None
            # Find the last Veena response
            for turn in reversed(chat_history):
                if turn.get("veena"):
                    last_veena_response = turn["veena"]
                    break
            
            if last_veena_response:
                # Clean the response (remove JSON metadata)
                clean_response = last_veena_response.split("```json")[0].strip()
                return f"Sure, let me repeat that. {clean_response}"
        
        return "I was asking about your life insurance policy renewal. Shall we continue?"
    
    def _handle_callback_request(self, response_template: str, session_data: Dict) -> str:
        """Handle callback scheduling request"""
        session_data["callback_requested"] = True
        return response_template
    
    def _handle_language_switch(self, user_input: str, response_template: str, session_data: Dict) -> str:
        """Handle language switching request"""
        # Detect requested language
        language_map = {
            "hindi": "Hindi",
            "marathi": "Marathi", 
            "gujarati": "Gujarati"
        }
        
        user_lower = user_input.lower()
        for lang_key, lang_name in language_map.items():
            if lang_key in user_lower:
                session_data["language_preference"] = lang_name
                return f"{response_template} Now, about your policy renewal..."
        
        return f"{response_template} Now, about your policy renewal..."
    
    def should_resume_main_flow(self, session_data: Dict, current_response: str) -> bool:
        """
        Determine if we should resume the main conversation flow.
        
        Args:
            session_data: Current session data
            current_response: The response that was just given
            
        Returns:
            Boolean indicating whether to resume main flow
        """
        interruption_context = session_data.get("interruption_context")
        if not interruption_context:
            return False
            
        # Check if enough interaction has happened to resume
        return True
    
    def get_intelligent_resume_stage(self, session_data: Dict, user_data: Dict) -> Optional[str]:
        """
        Intelligently determine the best stage to resume based on conversation context.
        
        Args:
            session_data: Current session data
            user_data: User profile data
            
        Returns:
            Stage name to resume, or None if no resumption needed
        """
        interruption_context = session_data.get("interruption_context")
        if not interruption_context:
            return None
            
        interrupted_stage = interruption_context.get("interrupted_stage")
        interruption_type = interruption_context.get("interruption_type")
        stage_history = interruption_context.get("stage_history", [])
        
        # If user showed payment commitment during interruption, jump to payment flow
        if interruption_type in ["renewal_commitment_interrupt", "early_payment_decision"]:
            return "payment_followup"
        
        # If user showed concerns during interruption, address them
        if interruption_type in ["ask_about_other_policies"] and len(stage_history) > 1:
            # If they were in policy_confirmation and asked about other policies, 
            # they might need more convincing
            if interrupted_stage == "policy_confirmation":
                return "explain_policy_loss"
        
        # For ambiguous responses, try to move to a clarification stage
        if interruption_type == "ambiguous_response_clarification":
            if interrupted_stage == "policy_confirmation":
                return "clarify_reactivation_intent"
        
        # Default: return to original interrupted stage
        return interrupted_stage
    
    def should_advance_stage_after_interruption(self, interruption_type: str, user_response: str) -> bool:
        """
        Determine if we should advance to next stage after handling interruption.
        
        Args:
            interruption_type: Type of interruption that was handled
            user_response: User's response after interruption
            
        Returns:
            Boolean indicating whether to advance stage
        """
        # If user showed positive intent, advance the conversation
        positive_indicators = ["yes", "ok", "proceed", "continue", "let's do it", "ready"]
        user_lower = user_response.lower() if user_response else ""
        
        if any(indicator in user_lower for indicator in positive_indicators):
            return True
        
        # For certain interruption types, advance regardless
        advancing_interruptions = ["renewal_commitment_interrupt", "early_payment_decision"]
        if interruption_type in advancing_interruptions:
            return True
            
        return False
    
    def get_resume_stage(self, session_data: Dict) -> Optional[str]:
        """
        Get the stage to resume after handling interruption.
        
        Args:
            session_data: Current session data
            
        Returns:
            Stage name to resume, or None if no resumption needed
        """
        interruption_context = session_data.get("interruption_context")
        if interruption_context:
            return interruption_context.get("interrupted_stage")
        return None
    
    def clear_interruption_context(self, session_data: Dict):
        """Clear interruption context after resumption"""
        if "interruption_context" in session_data:
            del session_data["interruption_context"]
    
    def is_critical_interruption(self, intent_name: str) -> bool:
        """
        Check if interruption is critical and should not allow resumption.
        
        Args:
            intent_name: Name of the interruption intent
            
        Returns:
            Boolean indicating if interruption is critical
        """
        if intent_name not in self.interruptible_intents:
            return False
            
        critical_intents = [
            "reschedule_callback", 
            "complaint_or_angry", 
            "early_payment_decision",
            "already_paid_interruption"
        ]
        return intent_name in critical_intents
    
    def is_in_interruption_flow(self, session_data: Dict) -> bool:
        """
        Check if we're currently in an interruption flow.
        
        Args:
            session_data: Current session data
            
        Returns:
            Boolean indicating if we're in interruption flow
        """
        return "current_interruption" in session_data
    
    def check_interruption_response(self, user_input: str, session_data: Dict) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Check if user input matches expected responses for current interruption.
        
        Args:
            user_input: User's input text
            session_data: Current session data
            
        Returns:
            Tuple of (is_match, response_text, action, next_stage)
        """
        current_interruption = session_data.get("current_interruption")
        if not current_interruption:
            return False, None, None, None
            
        intent_name = current_interruption.get("intent_name")
        if intent_name not in self.interruptible_intents:
            return False, None, None, None
            
        intent_data = self.interruptible_intents[intent_name]
        expected_responses = intent_data.get("expected_user_responses", {})
        
        if not expected_responses:
            return False, None, None, None
            
        user_input_lower = user_input.lower() if user_input else ""
        
        # Check for matches in expected responses
        for response_type, response_data in expected_responses.items():
            keywords = response_data.get("keywords", [])
            
            # Handle wildcard keyword "*" for catch-all responses
            if keywords == ["*"]:
                return True, response_data.get("response"), response_data.get("action"), response_data.get("next")
            
            # Check keyword matches
            if keywords:
                for keyword in keywords:
                    if keyword.lower() in user_input_lower:
                        return True, response_data.get("response"), response_data.get("action"), response_data.get("next")
        
        return False, None, None, None
    
    def handle_interruption_response(self, user_input, session_data, user_data):
        """
        Handle user response to an interruption.
        
        Args:
            user_input: User's input text
            session_data: Current session data
            user_data: User profile data
            
        Returns:
            Tuple of (response_text, metadata, should_continue)
        """
        current_interruption = session_data.get("current_interruption")
        if not current_interruption:
            return "I'm not sure what you're referring to. Let's continue with your policy renewal.", {}, True
        
        intent_name = current_interruption.get("intent_name")
        original_stage = current_interruption.get("original_stage")
        
        # Get interruption data
        intent_data = self.interruptible_intents.get(intent_name, {})
        expected_responses = intent_data.get("expected_user_responses", {})
        
        # Try to match user response to expected patterns with fuzzy matching
        user_input_lower = user_input.lower() if user_input else ""
        
        for response_type, response_data in expected_responses.items():
            keywords = response_data.get("keywords", [])
            if keywords and keywords != ["*"]:
                matched = False
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    
                    # Exact match
                    if keyword_lower in user_input_lower:
                        matched = True
                        break
                    
                    # Handle common typos for time-related words
                    elif keyword_lower == "tomorrow":
                        typo_variations = ["tommorow", "tomorow", "tomorrrow", "tommorrow"]
                        if any(typo in user_input_lower for typo in typo_variations):
                            matched = True
                            break
                    elif keyword_lower == "morning":
                        typo_variations = ["mornig", "morng", "moring"]
                        if any(typo in user_input_lower for typo in typo_variations):
                            matched = True
                            break
                    elif keyword_lower == "evening":
                        typo_variations = ["evenig", "evning", "eveng"]
                        if any(typo in user_input_lower for typo in typo_variations):
                            matched = True
                            break
                
                # Special handling for time specifications (like "12 30", "2:30", "10 am")
                if not matched and response_type == "provides_time":
                    time_patterns = [
                        r'\d{1,2}[\s:]\d{2}',  # "12 30", "12:30"
                        r'\d{1,2}\s?(am|pm)',   # "10 am", "2pm"
                        r'\d{1,2}[\s:]\d{2}\s?(am|pm)', # "12:30 pm"
                        r'(morning|afternoon|evening|night)', # time of day
                        r'(today|tomorrow|tommorow|tommorrow)', # day references
                    ]
                    if any(re.search(pattern, user_input_lower) for pattern in time_patterns):
                        matched = True
                
                if matched:
                    action = response_data.get("action", "return_to_main_flow")
                    
                    if action == "return_to_main_flow":
                        # ✅ IMPROVED: Clear interruption state and return to original stage
                        session_data.pop("current_interruption", None)
                        session_data.pop("interruption_context", None)
                        session_data["returned_from_interruption"] = True
                        
                        # ✅ CRITICAL FIX: Restore to original stage, not current
                        restored_stage = original_stage or session_data.get("conversation_stage", "greeting")
                        
                        response_text = response_data.get("response", "Great! Let's continue with your policy renewal.")
                        
                        return response_text, {
                            "intent": "interruption_closure",
                            "update": {
                                "conversation_stage": restored_stage  # Return to WHERE we were interrupted
                            },
                            "interruption_resolved": True,
                            "restored_to_stage": restored_stage
                        }, True
                    
                    elif action == "end_conversation":
                        # ✅ IMPROVED: For callback scheduling, store the callback info
                        session_data.pop("current_interruption", None)
                        session_data.pop("interruption_context", None)
                        
                        # Store callback information for comprehensive data
                        session_data["callback_scheduled"] = True
                        session_data["callback_time"] = user_input  # Store the user's specified time
                        session_data["callback_reason"] = "customer_request"
                        
                        return response_data.get("response", "Thank you for your time."), {
                            "intent": "end_conversation",
                            "update": {
                                "conversation_stage": "closure",
                                "callback_scheduled": True,
                                "next_call_scheduled": user_input
                            }
                        }, False
                    
                    elif action.startswith("next:"):
                        next_stage = action.split(":", 1)[1]
                        session_data.pop("current_interruption", None)
                        return response_data.get("response", ""), {
                            "intent": "interruption_redirect",
                            "update": {"conversation_stage": next_stage}
                        }, True
        
        # ✅ IMPROVED: Handle wildcard responses with proper fallback
        for response_type, response_data in expected_responses.items():
            if response_data.get("keywords") == ["*"]:
                action = response_data.get("action", "return_to_main_flow")
                
                if action == "return_to_main_flow":
                    session_data.pop("current_interruption", None)
                    session_data.pop("interruption_context", None)
                    session_data["returned_from_interruption"] = True
                    
                    restored_stage = original_stage or session_data.get("conversation_stage", "greeting")
                    
                    return response_data.get("response", "I understand. Let's continue with your policy renewal."), {
                        "intent": "interruption_closure",
                        "update": {"conversation_stage": restored_stage}
                    }, True
        
        # ✅ IMPROVED: Default fallback with proper stage restoration
        session_data.pop("current_interruption", None)
        session_data["returned_from_interruption"] = True
        restored_stage = original_stage or session_data.get("conversation_stage", "greeting")
        
        return "I understand. Let's continue with your policy renewal.", {
            "intent": "interruption_closure_default",
            "update": {"conversation_stage": restored_stage}
        }, True
