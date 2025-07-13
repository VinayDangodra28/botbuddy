# Interruption Management System for Veena

This system enables Veena to handle conversation interruptions gracefully while maintaining the main insurance renewal flow.

## 🧩 What are Interruptions?

Interruptions are off-script user responses that deviate from the expected conversation flow:

- **Off-topic queries**: "Can I get a new policy?" during renewal flow
- **Meta-requests**: "Can you repeat that?", "How do you know my number?"
- **Flow changes**: "I want to pay online" before payment options are presented
- **Emotional responses**: "I'm frustrated", "Connect me to your supervisor"

## 🏗️ Architecture

The interruption system consists of three main components:

### 1. `interruption_handler.py`
- **InterruptionHandler class**: Core logic for detecting and handling interruptions
- **Confidence scoring**: Keyword-based matching with confidence thresholds
- **Context preservation**: Saves conversation state for resumption
- **Critical vs non-critical classification**: Different handling for different interruption types

### 2. Enhanced `branches.json`
- **interruptible_intents section**: Defines all possible interruptions
- **Keywords**: Trigger phrases for each interruption type
- **Actions**: What to do when interruption is detected
- **Priority levels**: High/medium/low priority classification
- **Stage compatibility**: Which stages can be interrupted by which intents

### 3. Updated Agent Logic
- **Pre-processing step**: Check for interruptions before normal flow
- **Graceful transitions**: Smooth handling and resumption
- **State management**: Preserve context across interruptions

## 🔧 Configuration

### Adding New Interruption Types

In `branches.json`, add to the `interruptible_intents` section:

```json
"new_interruption_name": {
    "keywords": ["trigger", "phrases", "here"],
    "response": "How Veena should respond",
    "action": "what_action_to_take",
    "priority": "high|medium|low",
    "interruptible_stages": ["*"] // or specific stages
}
```

### Available Actions

- `acknowledge_and_redirect`: Acknowledge and return to main flow
- `repeat_last_response`: Repeat the previous Veena response
- `schedule_callback`: Handle callback requests
- `jump_to_payment_flow`: Skip to payment stage
- `jump_to_verification`: Skip to payment verification
- `switch_language`: Change conversation language
- `escalate_to_complaint_handling`: Handle complaints/anger
- `note_supervisor_request`: Log supervisor requests

### Priority Levels

- **High (1.2x weight)**: Critical interruptions (complaints, callbacks)
- **Medium (1.0x weight)**: Important but manageable (new policy questions)
- **Low (0.8x weight)**: Minor diversions (small talk)

## 🚀 Usage

### Basic Agent (Text-based)
```python
from agent import main
main()  # Now includes interruption handling
```

### Voice Agent
```python
from listen_agent import VoiceAgent
import asyncio

async def run_voice():
    agent = VoiceAgent()
    await agent.run_voice_conversation()

asyncio.run(run_voice())
```

### Testing
```python
from test_interruptions import test_interruption_scenarios, demo_conversation_with_interruptions

# Run automated tests
test_interruption_scenarios()

# Interactive demo
demo_conversation_with_interruptions()
```

## 📊 Flow Example

```
Stage: payment_inquiry
User: "Can you repeat that?"
→ Interruption detected: request_repeat (confidence: 0.85)
→ Action: repeat_last_response
→ Response: "Sure, let me repeat that. Could you please let me know why you haven't been able to pay the premium?"
→ Resume: Same stage (payment_inquiry)
```

## 🎯 Supported Interruption Types

| Intent | Triggers | Action | Critical |
|--------|----------|--------|----------|
| `request_repeat` | "repeat", "say again" | Repeat last response | No |
| `ask_about_other_policies` | "new policy", "another policy" | Acknowledge & redirect | No |
| `reschedule_callback` | "call later", "not now" | Schedule callback | Yes |
| `ask_how_you_got_number` | "how did you get my number" | Explain & redirect | No |
| `complaint_or_angry` | "angry", "frustrated" | Escalate to complaint handling | Yes |
| `early_payment_decision` | "want to pay", "pay now" | Jump to payment flow | Yes |
| `already_paid_interruption` | "already paid", "paid yesterday" | Jump to verification | Yes |
| `language_switch_request` | "hindi", "marathi", "gujarati" | Switch language | No |

## 🔄 Resumption Logic

### Non-Critical Interruptions
1. Handle the interruption
2. Save current conversation state
3. Provide appropriate response
4. Add transition phrase: "Now, let's continue with your policy renewal."
5. Resume at saved stage

### Critical Interruptions
1. Handle the interruption
2. Change conversation flow completely
3. No automatic resumption
4. Examples: Payment decisions, callbacks, complaints

## 📈 Confidence Scoring

The system uses keyword matching with confidence scoring:

- **Base confidence**: `matched_keywords / total_keywords`
- **Exact match bonus**: +0.3 for exact phrase matches
- **Priority weighting**: High=1.2x, Medium=1.0x, Low=0.8x
- **Threshold**: Default 0.6 (60% confidence required)

## 🛠️ Customization

### Adjusting Confidence Threshold
```python
is_interruption, intent, confidence = interruption_handler.detect_interruption(
    user_input, current_stage, confidence_threshold=0.7  # Stricter
)
```

### Adding Stage-Specific Interruptions
```json
"payment_specific_interruption": {
    "interruptible_stages": ["payment_inquiry", "payment_followup"],
    // ... other config
}
```

### Creating Custom Actions
Extend the `handle_interruption` method in `InterruptionHandler` class:

```python
elif action == "custom_action":
    return self._handle_custom_action(response_template, session_data), {
        "custom_metadata": True
    }, True
```

## 🐛 Debugging

Enable debug output to see interruption detection:
```
🔔 INTERRUPTION DETECTED: request_repeat (confidence: 0.85)
🚨 Critical interruption: reschedule_callback
🔄 Redirecting to existing branch: payment_followup (confidence: 0.72)
```

## 📋 Best Practices

1. **Keep interruption responses short** (under 35 words like main responses)
2. **Always include transition back to main flow** for non-critical interruptions
3. **Test edge cases** with the provided test script
4. **Monitor confidence scores** and adjust keywords as needed
5. **Use priority levels** to handle important interruptions first
6. **Preserve conversation context** for smooth resumption

## 🔮 Future Enhancements

- **LLM-based intent detection**: Use Gemini for more sophisticated interruption detection
- **Nested interruption handling**: Handle interruptions within interruptions
- **Learning system**: Automatically improve interruption handling based on usage
- **Voice-specific interruptions**: Handle "um", "uh", speech recognition errors
- **Sentiment-aware handling**: Adjust response tone based on user emotion
