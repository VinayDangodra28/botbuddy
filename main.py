"""
Voice Agent Module for BotBuddy
Voice-enabled conversation agent with customer selection
"""
from eleven_websocket import convert_single_text, play_audio_async
from dotenv import load_dotenv
from config_manager import ConfigManager
from session_manager import SessionManager
from response_analyzer import ResponseAnalyzer
from conversation_flow_controller import ConversationFlowController
from branches_manager import BranchesManager
from interruption_handler import InterruptionHandler
from enhanced_customer_manager import EnhancedCustomerManager
import os
import json
import re
import asyncio
import speech_recognition as sr

class VoiceAgent:
    def __init__(self, customer_data=None, api_key=None):
        # Load environment variables from .env file
        load_dotenv()
        
        # Initialize configuration
        self.config = ConfigManager()
        
        # Validate configuration
        config_issues = self.config.validate_config()
        if config_issues:
            print("⚠️ Configuration Issues:")
            for key, issue in config_issues.items():
                print(f"  - {key}: {issue}")

        # Initialize core components
        file_paths = self.config.get_file_paths()
        self.branches_manager = BranchesManager(file_paths["branches_file"], file_paths["suggestions_file"])
        self.interruption_handler = InterruptionHandler(self.branches_manager)
        self.response_analyzer = ResponseAnalyzer(self.branches_manager)

        # Initialize customer manager (comprehensive data system)
        self.customer_manager = EnhancedCustomerManager()

        # Initialize API configuration
        api_config = self.config.get_api_config()
        self.api_key = api_key or api_config["api_key"]
        
        # Speech recognition setup
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150  # Adjust as needed

        # Customer-specific data (will be set when customer is selected)
        self.current_customer = customer_data
        self.customer_id = None
        self.conversation_id = None
        self.session_manager = None
        self.conversation_controller = None
        self.user_data = None
        self.session_data = None
        
        # Initialize for selected customer if provided
        if customer_data:
            self._initialize_customer_session(customer_data)
    
    def _initialize_customer_session(self, customer_data):
        """Initialize session for a specific customer"""
        self.current_customer = customer_data
        self.customer_id = customer_data["id"]
        customer_name = customer_data["policy_holder_name"]
        
        print(f"\n🔄 Setting up voice conversation for {customer_name}...")
        
        # Start a new conversation in comprehensive data system
        self.conversation_id = self.customer_manager.start_conversation(self.customer_id)
        if not self.conversation_id:
            raise Exception("Failed to start conversation!")
        
        # Create customer-specific session files for compatibility
        user_data_file, session_data_file = self.customer_manager.create_session_files_for_customer(customer_data)
        
        # Initialize session manager for this customer
        self.session_manager = SessionManager(user_data_file, session_data_file)
        
        # Initialize conversation flow controller
        api_config = self.config.get_api_config()
        self.conversation_controller = ConversationFlowController(
            self.branches_manager, 
            self.interruption_handler, 
            self.response_analyzer, 
            api_config["api_key"]
        )
        
        # Get session and user data
        self.session_data = self.session_manager.get_session_data()
        self.user_data = self.session_manager.get_user_data()
        
        print(f"✅ Voice session initialized for {customer_name}")
    
    def save_session(self):
        """Save current session data to file and comprehensive data system"""
        try:
            if self.session_manager:
                self.session_manager.save_session()
            
            if self.customer_id and self.conversation_id and self.customer_manager:
                session_data = self.session_manager.get_session_data()
                self.customer_manager.update_session_in_comprehensive_data(
                    self.customer_id, self.conversation_id, session_data
                )
                
        except Exception as e:
            print(f"❌ Error saving session: {e}")

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
        """Process a single conversation turn with interruption handling using new architecture"""
        
        if not self.session_manager or not self.conversation_controller:
            print("❌ Error: Customer session not initialized. Please select a customer first.")
            return False
        
        current_stage = self.session_manager.get_current_stage()
        
        if user_input and user_input.strip():  # Only process if user provided input
            # Debug: Show current state if debug mode enabled
            if self.config.is_debug_mode():
                print(f"\n🔍 DEBUG: Current stage: {current_stage}")
                current_branch = self.branches_manager.read_branch(current_stage)
                if current_branch:
                    expected_types = list(current_branch.get("expected_user_responses", {}).keys())
                    print(f"🔍 DEBUG: Expected response types: {expected_types}")
            
            # Process conversation turn with interruption handling
            bot_response, metadata, conversation_continues = self.conversation_controller.process_conversation_turn(
                user_input, current_stage, self.user_data, self.session_data
            )
            
            print(f"🤖 Veena: {bot_response}")
            
            # Add to comprehensive data system
            self.customer_manager.add_chat_message(self.customer_id, self.conversation_id, user_input, bot_response, metadata)
        
        else:
            # Empty input - prompt user to respond instead of calling Gemini
            print("Please provide a response to continue the conversation.")
            return True  # Continue conversation

        # Update session data based on metadata
        if "update" in metadata:
            self.session_manager.update_session(metadata["update"])
            self.customer_manager.update_session_in_comprehensive_data(self.customer_id, self.conversation_id, metadata["update"])
        if "intent" in metadata:
            self.session_manager.update_session({"last_intent": metadata["intent"]})
            self.customer_manager.update_session_in_comprehensive_data(self.customer_id, self.conversation_id, {"last_intent": metadata["intent"]})

        self.session_manager.add_to_chat_history(user_input, bot_response)
        
        if self.config.should_auto_save():
            self.session_manager.save_session()

        # Check if we've transitioned to a closure branch and need to display its final message
        current_stage_after_update = self.session_manager.get_current_stage()
        closure_branches = {"closure", "payment_success_closure", "complaint_resolution_closure", "schedule_callback"}
        
        if (current_stage_after_update in closure_branches and 
            current_stage_after_update != current_stage):  # We just transitioned to a closure branch
            
            # Get the closure branch's bot_prompt and display it
            closure_branch = self.branches_manager.read_branch(current_stage_after_update)
            if closure_branch and "bot_prompt" in closure_branch:
                final_message = closure_branch["bot_prompt"]
                # Replace any placeholders with user data
                for key, value in self.user_data.items():
                    final_message = final_message.replace(f"{{{key}}}", str(value))
                
                print(f"🤖 Veena: {final_message}")
                
                # Add this final message to chat history and comprehensive data
                self.session_manager.add_to_chat_history(None, final_message)
                self.customer_manager.add_chat_message(self.customer_id, self.conversation_id, None, final_message, 
                                               {"stage": current_stage_after_update, "final_closure_message": True})
                
                # Convert to speech
                await self.text_to_speech(final_message)

        # Convert to speech
        if bot_response:
            await self.text_to_speech(bot_response)
        
        return not self.session_manager.is_conversation_complete()

    async def run_voice_conversation(self):
        """Main voice conversation loop with customer data integration"""
        if not self.current_customer:
            print("❌ Error: No customer selected for voice conversation.")
            return
        
        customer_name = self.current_customer["policy_holder_name"]
        
        print("🤖 Voice Agent Started!")
        print(f"📞 Calling {customer_name}...")
        print("💡 Tip: Speak clearly after the listening prompt")
        
        # === Check if this is a callback continuation and handle appropriately ===
        is_callback = self.session_data.get("is_callback", False)
        if is_callback and self.session_data.get("continued_from_callback"):
            callback_time = self.session_data.get("callback_time", "scheduled time")
            callback_greeting = f"Hello! This is Veena calling back as scheduled at {callback_time}. Are you available to continue our conversation about your policy?"
            print(f"🤖 Veena: {callback_greeting}")
            
            # Add to comprehensive data system
            self.customer_manager.add_chat_message(
                self.customer_id, self.conversation_id, None, callback_greeting, {
                    "stage": self.session_data.get("conversation_stage"),
                    "callback_continuation": True
                }
            )
            
            # Update session data to indicate callback has been handled
            callback_updates = {
                "callback_handled": True,
                "callback_time": callback_time,
                "callback_continuation": True
            }
            self.session_manager.update_session(callback_updates)
            self.customer_manager.update_session_in_comprehensive_data(
                self.customer_id, self.conversation_id, callback_updates
            )
            
            self.session_manager.add_to_chat_history(None, callback_greeting)
            self.session_manager.save_session()
            await self.text_to_speech(callback_greeting)
            
            # Let the user know which stage we're continuing from
            current_stage = self.session_data.get("conversation_stage")
            print(f"\n🔄 Continuing conversation from: {current_stage}")
            
        # === Initial Greeting by Veena if stage is "greeting" and not a callback ===
        elif self.session_data.get("conversation_stage") == "greeting":
            # Use static greeting from branches.json instead of calling Gemini
            greeting_branch = self.branches_manager.read_branch("greeting")
            if greeting_branch and "bot_prompt" in greeting_branch:
                bot_response = greeting_branch["bot_prompt"]
                # Replace placeholders with user data
                for key, value in self.user_data.items():
                    bot_response = bot_response.replace(f"{{{key}}}", str(value))
            else:
                # Fallback greeting if branch not found
                bot_response = f"Hello and very Good Morning Sir, May I speak with {self.user_data.get('policy_holder_name', 'you')}?"
            
            print(f"🤖 Veena: {bot_response}")

            # Add to comprehensive data system
            self.customer_manager.add_chat_message(self.customer_id, self.conversation_id, None, bot_response, {"stage": "greeting"})

            # For greeting, we don't need to extract metadata from Gemini response
            # Just set basic metadata manually
            metadata = {"stage": "greeting", "intent": "initial_greeting"}
            self.session_manager.update_session({"last_intent": "initial_greeting"})
            self.customer_manager.update_session_in_comprehensive_data(self.customer_id, self.conversation_id, {"last_intent": "initial_greeting"})

            self.session_manager.add_to_chat_history(None, bot_response)
            self.session_manager.save_session()
            await self.text_to_speech(bot_response)

        # Main conversation loop
        while True:
            user_input = await self.speech_to_text()
            
            # Handle special commands
            if user_input and user_input.lower() in ['quit', 'exit', 'end']:
                print("📞 Ending conversation...")
                self.customer_manager.end_conversation(self.customer_id, self.conversation_id, "user_terminated")
                break
            
            if user_input:
                continue_conversation = await self.process_conversation_turn(user_input)
                if not continue_conversation:
                    print(f"✅ Conversation with {customer_name} completed.")
                    self.customer_manager.end_conversation(self.customer_id, self.conversation_id, "successful")
                    
                    # Show pending suggestions summary
                    pending_suggestions = self.branches_manager.get_pending_suggestions()
                    pending_ops = pending_suggestions.get("pending_operations", [])
                    if pending_ops:
                        print(f"\n💡 Veena has made {len(pending_ops)} suggestions to improve future conversations.")
                        print("Use 'apply_suggestions.py' to review and apply these suggestions to branches.json")
                    break
            else:
                print("❓ No input received. Try speaking again or press Ctrl+C to exit.")

def select_customer():
    """Allow user to select which customer to call (voice version)"""
    customer_manager = EnhancedCustomerManager()
    
    while True:
        print("\n" + "="*50)
        print("      🎙️  BotBuddy Voice Customer Selection")
        print("="*50)
        
        # Display customers list
        customer_manager.display_customers_list()
        
        print("\nOptions:")
        print("1. Enter customer number (1, 2, 3...)")
        print("2. Enter customer name")
        print("3. Enter customer ID")
        print("4. Type 'refresh' to refresh the list")
        print("5. Type 'exit' to quit")
        
        user_choice = input("\n📞 Select customer to call: ").strip()
        
        if user_choice.lower() == 'exit':
            return None
        
        if user_choice.lower() == 'refresh':
            continue
        
        selected_customer = customer_manager.get_customer_for_conversation(user_choice)
        
        if selected_customer:
            customer_name = selected_customer['policy_holder_name']
            policy_number = selected_customer['policy_number']
            outstanding = selected_customer['outstanding_amount']
            
            print(f"\n✅ Selected Customer:")
            print(f"   Name: {customer_name}")
            print(f"   Policy: {policy_number}")
            print(f"   Outstanding: {outstanding}")
            
            confirm = input(f"\n📞 Start voice call with {customer_name}? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                return selected_customer
            else:
                continue
        else:
            print(f"\n❌ Customer '{user_choice}' not found. Please try again.")


async def run_voice_conversation_for_customer(customer):
    """Run voice conversation for selected customer"""
    customer_name = customer["policy_holder_name"]
    
    print(f"\n🔄 Setting up voice conversation for {customer_name}...")
    
    try:
        # Create voice agent with customer data
        voice_agent = VoiceAgent(customer_data=customer)
        
        print(f"\n📞 Starting voice conversation with {customer_name}...")
        print("="*60)
        
        # Start the voice conversation
        await voice_agent.run_voice_conversation()
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Voice conversation with {customer_name} interrupted by user.")
        if 'voice_agent' in locals() and voice_agent.customer_id and voice_agent.conversation_id:
            voice_agent.customer_manager.end_conversation(
                voice_agent.customer_id, voice_agent.conversation_id, "interrupted"
            )
    
    except Exception as e:
        print(f"\n❌ Error during voice conversation with {customer_name}: {e}")
        if 'voice_agent' in locals() and voice_agent.customer_id and voice_agent.conversation_id:
            voice_agent.customer_manager.end_conversation(
                voice_agent.customer_id, voice_agent.conversation_id, "error", {"error": str(e)}
            )
    
    finally:
        # Clean up customer-specific session files
        if 'voice_agent' in locals() and voice_agent.customer_id:
            voice_agent.customer_manager.cleanup_customer_session_files(voice_agent.customer_id)


async def main():
    """Main function to run the voice agent with customer selection"""
    print("🎙️ Welcome to BotBuddy Voice Agent!")
    
    while True:
        # Customer selection
        selected_customer = select_customer()
        
        if not selected_customer:
            print("👋 Goodbye!")
            break
        
        # Run voice conversation for selected customer
        await run_voice_conversation_for_customer(selected_customer)
        
        # Ask if user wants to call another customer
        another_call = input("\n📞 Do you want to call another customer? (y/n): ").strip().lower()
        if another_call not in ['y', 'yes']:
            print("👋 Thanks for using BotBuddy Voice Agent!")
            break

if __name__ == "__main__":
    asyncio.run(main())
