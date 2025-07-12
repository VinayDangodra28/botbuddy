import json

# Load conversation branches once
with open("branches.json", 'r', encoding='utf-8') as f:
    BRANCHES = json.load(f)

def load_suggestions_context():
    """Load suggestions from suggestions.json for context"""
    try:
        with open("suggestions.json", 'r', encoding='utf-8') as f:
            suggestions = json.load(f)
            return suggestions.get("pending_operations", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def render_template(template: str, user_data: dict) -> str:
    """Replace placeholders in bot prompts using user_data"""
    if not template:
        return ""
    for key, value in user_data.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def build_prompt(user_input, user_data, session_data):
    stage = session_data.get("conversation_stage", "greeting")
    branch = BRANCHES.get(stage, {})
    
    # If stage doesn't exist in branches, default to greeting
    if not branch:
        stage = "greeting"
        branch = BRANCHES.get("greeting", {})

    bot_prompt = render_template(branch.get("bot_prompt", ""), user_data)
    
    # Check for language-specific prompt
    language_pref = session_data.get("language_preference", "English")
    if language_pref != "English":
        lang_prompt = get_language_specific_prompt(stage, language_pref)
        if lang_prompt:
            bot_prompt = render_template(lang_prompt, user_data)
    
    intent = branch.get("intent", "unknown_intent")
    expected_responses = branch.get("expected_user_responses", {})

    # Detect language preference
    language_pref = detect_language_preference(user_input)
    if language_pref != "English":
        session_data["language_preference"] = language_pref

    # Determine next stage based on user input
    next_stage = get_next_stage(stage, user_input, user_data, session_data)
    
    # Get scripted response if available
    scripted_response = get_scripted_response(stage, user_input, user_data)
    if scripted_response:
        scripted_response = render_template(scripted_response, user_data)

    # Load Veena's suggestions context
    suggestions_context = ""
    pending_suggestions = load_suggestions_context()
    if pending_suggestions:
        suggestions_context = f"\n\n**VEENA'S PENDING SUGGESTIONS (for context only):**\nVeena has suggested {len(pending_suggestions)} improvements to handle various customer scenarios better. These suggestions will be applied to the conversation flow when approved.\n"

    # Format recent conversation history (last 2-3 exchanges)
    history_lines = []
    recent_history = session_data.get("chat_history", [])[-3:]
    for turn in recent_history:
        if turn.get("user"):
            history_lines.append(f'User: {turn["user"]}')
        if turn.get("veena"):
            clean_response = turn["veena"].split("```")[0].strip()
            history_lines.append(f'Veena: {clean_response}')
    
    conversation_history = "\n".join(history_lines) if history_lines else "No previous conversation"

    # Build comprehensive master prompt
    prompt = f"""
You are **Veena**, a female insurance agent for ValuEnable Life Insurance. You MUST follow the conversation script EXACTLY as provided below.

**STRICT INSTRUCTIONS - FOLLOW EXACTLY:**
1. Use MAXIMUM 35 simple English words to respond
2. ALWAYS end with a question to keep conversation flowing
3. If customer requests different language (Hindi, Marathi, Gujarati), switch immediately
4. FOLLOW THE CONVERSATION FLOW STRICTLY - Do not deviate from the script
5. Use the EXACT response provided in the script for this stage
6. Be empathetic but persistent about premium payment

**MANDATORY SCRIPT TO FOLLOW:**
Current Stage: {stage}
Required Response Template: "{bot_prompt}"
{f'Exact Scripted Response: "{scripted_response}"' if scripted_response else 'No specific scripted response - use template above'}

**CUSTOMER INFORMATION:**
- Name: {user_data.get('policy_holder_name', 'Sir/Madam')}
- Policy: {user_data.get('product_name', 'Life Insurance')} (#{user_data.get('policy_number', 'N/A')})
- Outstanding Amount: {user_data.get('outstanding_amount', 'N/A')}
- Due Date: {user_data.get('premium_due_date', 'N/A')}
- Language: {session_data.get('language_preference', 'English')}

**CONVERSATION HISTORY:**
{conversation_history}

**USER'S CURRENT INPUT:**
"{user_input if user_input else "Starting conversation"}"

**EXPECTED USER RESPONSES FOR THIS STAGE:**
{', '.join(expected_responses.keys()) if expected_responses else 'Any response'}{suggestions_context}

**SCRIPT-BASED RESPONSE RULES:**
- If there's an "Exact Scripted Response" above, use it WORD-FOR-WORD (just fill in customer data)
- If only template provided, adapt it slightly but stay within 35 words
- If user response matches expected patterns, follow the script flow exactly
- If user mentions financial problems → suggest EMI/payment plans
- If user is busy → offer to reschedule  
- If user refuses → use gentle rebuttals about policy benefits
- ALWAYS guide conversation towards payment or callback scheduling
- DO NOT deviate from the conversation script or improvise responses

**CRITICAL: You MUST follow the script exactly. If scripted response exists, use it verbatim with customer data filled in.**

RESPOND EXACTLY as Veena would according to the script, then provide JSON:

```json
{{
  "intent": "{intent}",
  "update": {{
    "conversation_stage": "{next_stage}",
    "language_preference": "{session_data.get('language_preference', 'English')}",
    "user_reason_for_non_payment": "extract_if_mentioned_in_user_input"
  }}
}}
```"""
    return prompt


def get_next_stage(current_stage, user_input, user_data, session_data):
    """
    Determine the next conversation stage based on current stage and user response
    Dynamically uses branches.json instead of hardcoded logic
    """
    branch = BRANCHES.get(current_stage, {})
    expected_responses = branch.get("expected_user_responses", {})
    
    user_input_lower = user_input.lower() if user_input else ""
    
    # Global checks first (these can happen from any stage)
    if any(word in user_input_lower for word in ["financial", "money", "problem", "issue", "difficult", "difficulties"]):
        if current_stage in ["policy_confirmation", "explain_policy_loss"]:
            return "financial_problem_handling"
    
    if any(word in user_input_lower for word in ["busy", "later", "not good time", "call back", "call later"]):
        return "check_reschedule"
    
    # Dynamic stage determination based on keywords from branches.json
    if expected_responses:
        best_match = find_best_response_match(user_input, expected_responses)
        if best_match:
            response_data = expected_responses[best_match]
            next_stage = response_data.get("next")
            if next_stage:
                return next_stage
    
    # Fallback to current stage if no match found
    return current_stage


def detect_language_preference(user_input):
    """
    Detect if user wants to switch language
    """
    if not user_input:
        return "English"
    
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ["hindi", "हिंदी", "हिन्दी"]):
        return "Hindi"
    elif any(word in user_input_lower for word in ["marathi", "मराठी"]):
        return "Marathi"
    elif any(word in user_input_lower for word in ["gujarati", "ગુજરાતી"]):
        return "Gujarati"
    
    return "English"


def get_language_specific_prompt(stage, language="English"):
    """
    Get stage-specific prompts in different languages
    """
    language_prompts = {
        "Hindi": {
            "greeting": "नमस्ते, मैं वीणा हूं ValuEnable Life Insurance से। क्या मैं {policy_holder_name} से बात कर सकती हूं?",
            "closure": "अधिक जानकारी के लिए हमारी हेल्पलाइन 1800 209 7272 पर कॉल करें। धन्यवाद!"
        },
        "Marathi": {
            "greeting": "नमस्कार, मी वीणा आहे ValuEnable Life Insurance कंपनीतून। मी {policy_holder_name} शी बोलू शकते का?",
            "closure": "अधिक माहितीसाठी आमच्या हेल्पलाइनवर 1800 209 7272 वर कॉल करा। धन्यवाद!"
        },
        "Gujarati": {
            "greeting": "નમસ્તે, હું વીણા છું ValuEnable Life Insurance થી। શું હું {policy_holder_name} સાથે વાત કરી શકું?",
            "closure": "વધુ માહિતી માટે અમારી હેલ્પલાઈન 1800 209 7272 પર કોલ કરો। આભાર!"
        }
    }
    
    if language in language_prompts and stage in language_prompts[language]:
        return language_prompts[language][stage]
    return None


def get_scripted_response(current_stage, user_input, user_data):
    """
    Get the exact scripted response based on current stage and user input
    Dynamically matches keywords from branches.json instead of hardcoded conditions
    """
    branch = BRANCHES.get(current_stage, {})
    expected_responses = branch.get("expected_user_responses", {})
    
    if not expected_responses:
        return None
    
    user_input_lower = user_input.lower() if user_input else ""
    
    # Use the improved matching algorithm
    best_match = find_best_response_match(user_input, expected_responses)
    
    if best_match:
        response_data = expected_responses[best_match]
        response = response_data.get("response")
        if response:  # Only return if there's an actual response
            return response
    
    return None


def score_keyword_match(user_input_lower, keywords):
    """
    Calculate a matching score based on how many keywords match
    Returns the number of matched keywords and total keyword count
    """
    if not keywords:
        return 0, 0
    
    matched_keywords = sum(1 for keyword in keywords if keyword.lower() in user_input_lower)
    return matched_keywords, len(keywords)


def find_best_response_match(user_input, expected_responses):
    """
    Find the best matching response based on keyword scoring
    Returns the response_type with highest match score
    """
    if not expected_responses or not user_input:
        return None
        
    user_input_lower = user_input.lower()
    best_match = None
    best_score = 0
    best_ratio = 0
    
    for response_type, response_data in expected_responses.items():
        keywords = response_data.get("keywords", [])
        if keywords:
            matched_count, total_count = score_keyword_match(user_input_lower, keywords)
            match_ratio = matched_count / total_count if total_count > 0 else 0
            
            # Prioritize by number of matched keywords, then by match ratio
            if matched_count > best_score or (matched_count == best_score and match_ratio > best_ratio):
                best_match = response_type
                best_score = matched_count
                best_ratio = match_ratio
    
    return best_match if best_score > 0 else None


# -----------------------------
# ✅ Example usage (proper workflow)
# -----------------------------

if __name__ == "__main__":
    # Simulated runtime inputs for premium reminder call
    user_input = "Yes, this is Pratik speaking"
    user_data = {
        "policy_holder_name": "Pratik Jadhav",
        "policy_number": "VE12345678",
        "product_name": "ValuEnable Shield Plan",
        "outstanding_amount": "₹10,000",
        "premium_due_date": "2025-06-15"
    }
    session_data = {
        "conversation_stage": "greeting",
        "language_preference": "English",
        "chat_history": []
    }

    # Generate prompt for Gemini
    prompt = build_prompt(user_input, user_data, session_data)

    # Simulate Gemini response
    bot_response = "Hello Pratik! I'm Veena from ValuEnable Life Insurance. Your policy premium of ₹10,000 is overdue since June 15th. Can we discuss this? ```json\n{\"intent\":\"initial_greeting\",\"update\":{\"conversation_stage\":\"policy_confirmation\",\"language_preference\":\"English\"}}```"

    # ✅ Ensure chat_history is initialized
    session_data.setdefault("chat_history", []).append({
        "user": user_input,
        "veena": bot_response
    })

    print("Generated Master Prompt:\n", prompt)
    print("\nNext stage determined:", get_next_stage("greeting", user_input, user_data, session_data))
    print("\nSession Chat History:", session_data["chat_history"])
