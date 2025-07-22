"""
Response Analysis Module
Handles response matching, branch detection, and conversation flow analysis
"""
import json
import re
from typing import Dict, Any, Optional, Tuple
from branches_manager import BranchesManager


class ResponseAnalyzer:
    """Analyzes user responses and determines appropriate conversation flow"""
    
    def __init__(self, branches_manager: BranchesManager):
        self.branches_manager = branches_manager
    
    def extract_metadata(self, response: str) -> Dict[str, Any]:
        """Extract JSON metadata from response"""
        try:
            match = re.search(r'```json\n({.*?})\n```', response, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception as e:
            print(f"JSON extraction error: {e}")
        return {}
    
    def fix_currency_formatting(self, text: str) -> str:
        """Fix double rupee symbol issue and other currency formatting problems"""
        if not text:
            return text
        
        # Replace ₹₹ with ₹
        text = re.sub(r'₹₹', '₹', text)
        
        # Ensure proper spacing around currency
        text = re.sub(r'₹(\d)', r'₹\1', text)
        
        return text
    
    def check_if_response_matches_expected(self, user_input: str, current_stage: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
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
    
    def find_appropriate_existing_branch(self, user_input: str, current_stage: str) -> Tuple[Optional[str], float]:
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
            
            # Scheduling and timing - reschedule_callback has higher priority than schedule_callback
            "reschedule_callback": ["can we speak", "speak tomorrow", "speak later", "call later", "not now", "busy", "different time", "another time", "reschedule", "not good time"],
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
                
            # Calculate match score with fuzzy matching for common typos
            matches = 0
            for keyword in keywords:
                if keyword in user_input_lower:
                    matches += 1
                # Handle common typos and variations for scheduling keywords
                elif branch_name == "schedule_callback":
                    # Common typos for "tomorrow"
                    if keyword == "tomorrow" and any(variant in user_input_lower for variant in ["tommorow", "tomorow", "tomorrrow", "tommorrow"]):
                        matches += 1
                    # Variations for "evening"  
                    elif keyword == "evening" and any(variant in user_input_lower for variant in ["evenig", "evning", "eveng"]):
                        matches += 1
                    # Variations for "morning"
                    elif keyword == "morning" and any(variant in user_input_lower for variant in ["mornig", "morng", "moring"]):
                        matches += 1
                # Handle reschedule_callback variations
                elif branch_name == "reschedule_callback":
                    if keyword == "speak tomorrow" and any(variant in user_input_lower for variant in ["speak tommorow", "speak tomorow", "talk tomorrow", "talk tommorow"]):
                        matches += 1
                    elif keyword == "can we speak" and any(variant in user_input_lower for variant in ["can we talk", "could we speak", "could we talk"]):
                        matches += 1
                    elif keyword == "call back" and any(variant in user_input_lower for variant in ["callback", "call-back", "call me back", "call later"]):
                        matches += 1
                    elif keyword == "different time" and any(variant in user_input_lower for variant in ["other time", "another time", "diff time"]):
                        matches += 1
            if matches > 0:
                # Score based on keyword matches and keyword specificity
                base_score = matches / len(keywords)
                
                # Apply priority boost for key intent matches
                priority_boost = 1.0
                if branch_name == "reschedule_callback" and any(phrase in user_input_lower for phrase in ["can we speak", "speak tomorrow", "not good time"]):
                    priority_boost = 1.5  # 50% boost for clear reschedule intent
                elif branch_name == "schedule_callback" and "tomorrow" in user_input_lower:
                    # Only boost if it's a direct time specification without reschedule context
                    if not any(reschedule_phrase in user_input_lower for reschedule_phrase in ["can we", "speak", "not now", "busy"]):
                        priority_boost = 1.2
                
                final_score = base_score * priority_boost
                if final_score > highest_score:
                    highest_score = final_score
                    best_match = branch_name
        
        # Only return match if confidence is reasonable
        if highest_score >= 0.1:  # At least 10% keyword match
            return best_match, highest_score
        
        return None, 0
