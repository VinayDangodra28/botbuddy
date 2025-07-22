# BotBuddy - AI Voice Agent for Insurance Collection

## Overview

BotBuddy is an intelligent voice-enabled conversation agent specifically designed for insurance premium collection calls. The system uses advanced AI to conduct natural conversations with customers, handle various scenarios, and maintain conversation flow.

## Main Files

### Primary Entry Points

- **`main.py`** - Main voice agent with speech-to-text and text-to-speech capabilities
- **`agent.py`** - Text-based conversation agent

### Core Components

- **`config_manager.py`** - Configuration management and validation
- **`session_manager.py`** - Session and user data management
- **`conversation_flow_controller.py`** - Main conversation logic controller
- **`branches_manager.py`** - Conversation branch and flow management
- **`response_analyzer.py`** - AI response analysis and metadata extraction
- **`interruption_handler.py`** - Handles conversation interruptions and context switching
- **`enhanced_customer_manager.py`** - Advanced customer data management
- **`customer_manager.py`** - Basic customer operations
- **`prompt_builder.py`** - AI prompt construction utilities
- **`gemini_api.py`** - Google Gemini AI API interface
- **`eleven_websocket.py`** - ElevenLabs text-to-speech integration

## Data Files

### Configuration

- **`.env`** - Environment variables (API keys, etc.)
- **`requirements.txt`** - Python dependencies

### Core Data

- **`branches.json`** - Conversation flow definitions and branches
- **`customers.json`** - Customer database
- **`botbuddy_comprehensive_data.json`** - Comprehensive conversation history
- **`botbuddy_data_template.json`** - Data structure template

### Session Data

- **`user_data.json`** - Current user/customer data
- **`session_data.json`** - Current conversation session state
- **`suggestions.json`** - AI-generated improvement suggestions

## Utilities

### Data Management

- **`reset_data.py`** - Reset system to initial state
- **`data_reset_utility.py`** - Advanced data reset utilities
- **`comprehensive_data_manager.py`** - Manage comprehensive data system
- **`customer_utility.py`** - Customer data utilities

### Validation & Improvement

- **`validate_branches.py`** - Validate conversation branch structure
- **`apply_suggestions.py`** - Apply AI-generated improvements

## Setup Instructions

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```
2. **Configure Environment**

   - Update `.env` file with your API keys:
     - `GEMINI_API_KEY` - Google Gemini AI API key
     - `ELEVENLABS_API_KEY` - ElevenLabs TTS API key (for voice agent)
3. **Initialize Data**

   ```bash
   python reset_data.py
   ```

## Usage

### Voice Agent (Primary)

```bash
python main.py
```

- Provides full voice interaction
- Speech-to-text input
- Text-to-speech output
- Customer selection interface

### Text Agent (Alternative)

```bash
python agent.py
```

- Text-based interaction
- Useful for testing and debugging

## Features

### Core Capabilities

- **Multi-customer Support** - Handle different customers with personalized data
- **Dynamic Conversation Flow** - AI-driven conversation branching
- **Voice Integration** - Natural speech interaction
- **Interruption Handling** - Context-aware conversation management
- **Learning System** - AI generates improvements from conversations

### Conversation Scenarios

- Policy confirmation and details
- Payment collection and processing
- Objection handling and rebuttals
- Financial problem resolution
- Callback scheduling
- Customer service scenarios

### Data Persistence

- Comprehensive conversation history
- Customer interaction tracking
- Session continuity across calls
- AI learning and improvement suggestions

## System Architecture

The system follows a modular architecture:

1. **Interface Layer** (`main.py`, `agent.py`)
2. **Core Logic** (`conversation_flow_controller.py`)
3. **AI Integration** (`gemini_api.py`, `response_analyzer.py`)
4. **Data Management** (`session_manager.py`, `enhanced_customer_manager.py`)
5. **Flow Control** (`branches_manager.py`, `interruption_handler.py`)
6. **Utilities** (various utility files)

## Validation & Testing

- Run `validate_branches.py` to check conversation flow integrity
- Use `apply_suggestions.py` to implement AI-generated improvements
- Reset system state with `reset_data.py` when needed

## Notes

- Ensure all API keys are properly configured in `.env`
- The system requires internet connectivity for AI and TTS services
- Customer data can be customized in `customers.json`
- Conversation flows can be modified in `branches.json`

## Competition Submission

This folder contains all essential files needed to run the BotBuddy system independently. The system demonstrates advanced AI conversation management, voice integration, and intelligent customer interaction capabilities suitable for insurance premium collection scenarios.
