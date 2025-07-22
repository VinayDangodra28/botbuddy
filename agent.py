"""
Main Agent Module
Entry point for the BotBuddy conversation agent
"""
from config_manager import ConfigManager
from session_manager import SessionManager
from response_analyzer import ResponseAnalyzer
from conversation_flow_controller import ConversationFlowController
from branches_manager import BranchesManager
from interruption_handler import InterruptionHandler
from customer_manager import CustomerManager
from prompt_builder import build_prompt
from gemini_api import send_to_gemini

# Initialize configuration
config = ConfigManager()

# Validate configuration
config_issues = config.validate_config()
if config_issues:
    print("⚠️ Configuration Issues:")
    for key, issue in config_issues.items():
        print(f"  - {key}: {issue}")

# Initialize core components
file_paths = config.get_file_paths()
branches_manager = BranchesManager(file_paths["branches_file"], file_paths["suggestions_file"])
interruption_handler = InterruptionHandler(branches_manager)
response_analyzer = ResponseAnalyzer(branches_manager)

# Initialize customer manager (comprehensive data system)
from enhanced_customer_manager import EnhancedCustomerManager
customer_manager = EnhancedCustomerManager()

# Initialize API configuration
api_config = config.get_api_config()

def select_customer():
    """Allow user to select which customer to call"""
    while True:
        print("\n" + "="*50)
        print("         🤖 BotBuddy Customer Selection")
        print("="*50)
        
        # Display customers list
        customer_manager.display_customers_list()
        
        print("\nOptions:")
        print("1. Enter customer number (1, 2, 3...)")
        print("2. Enter customer name")
        print("3. Enter customer ID")
        print("4. Type 'refresh' to refresh the list")
        print("5. Type 'exit' to quit")
        
        user_choice = input("\n👤 Select customer to call: ").strip()
        
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
            
            confirm = input(f"\n📞 Start conversation with {customer_name}? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                return selected_customer
            else:
                continue
        else:
            print(f"\n❌ Customer '{user_choice}' not found. Please try again.")


def run_conversation_for_customer(customer):
    """Run conversation for selected customer"""
    customer_id = customer["id"]
    customer_name = customer["policy_holder_name"]
    
    print(f"\n🔄 Setting up conversation for {customer_name}...")
    
    # Start a new conversation in comprehensive data system
    conversation_id = customer_manager.start_conversation(customer_id)
    if not conversation_id:
        print("❌ Failed to start conversation!")
        return
    
    # Create customer-specific session files for compatibility
    user_data_file, session_data_file = customer_manager.create_session_files_for_customer(customer)
    
    # Initialize session manager for this customer
    session_manager = SessionManager(user_data_file, session_data_file)
    
    # Initialize conversation flow controller
    conversation_controller = ConversationFlowController(
        branches_manager, 
        interruption_handler, 
        response_analyzer, 
        api_config["api_key"]
    )
    
    try:
        print(f"\n📞 Starting conversation with {customer_name}...")
        print("="*60)
        
        # Get session and user data
        session_data = session_manager.get_session_data()
        user_data = session_manager.get_user_data()
        
        # === Check if this is a callback continuation and handle appropriately ===
        is_callback = session_data.get("is_callback", False)
        if is_callback and session_data.get("continued_from_callback"):
            callback_time = session_data.get("callback_time", "scheduled time")
            callback_greeting = f"Hello! This is Veena calling back as scheduled at {callback_time}. Are you available to continue our conversation about your policy?"
            print(callback_greeting)
            
            # Add to comprehensive data system
            customer_manager.add_chat_message(customer_id, conversation_id, None, callback_greeting, {
                "stage": session_data.get("conversation_stage"),
                "callback_continuation": True
            })
            
            # Update session data to indicate callback has been handled
            callback_updates = {
                "callback_handled": True,
                "callback_time": callback_time,
                "callback_continuation": True
            }
            session_manager.update_session(callback_updates)
            customer_manager.update_session_in_comprehensive_data(customer_id, conversation_id, callback_updates)
            
            session_manager.add_to_chat_history(None, callback_greeting)
            session_manager.save_session()
            
            # Let the user know which stage we're continuing from
            current_stage = session_data.get("conversation_stage")
            print(f"\n🔄 Continuing conversation from: {current_stage}")
            
        # === Initial Greeting by Veena if stage is "greeting" and not a callback ===
        elif session_data.get("conversation_stage") == "greeting":
            # Use static greeting from branches.json instead of calling Gemini
            greeting_branch = branches_manager.read_branch("greeting")
            if greeting_branch and "bot_prompt" in greeting_branch:
                bot_response = greeting_branch["bot_prompt"]
                # Replace placeholders with user data
                for key, value in user_data.items():
                    bot_response = bot_response.replace(f"{{{key}}}", str(value))
            else:
                # Fallback greeting if branch not found
                bot_response = f"Hello and very Good Morning Sir, May I speak with {user_data.get('policy_holder_name', 'you')}?"
            
            print(bot_response)

            # Add to comprehensive data system
            customer_manager.add_chat_message(customer_id, conversation_id, None, bot_response, {"stage": "greeting"})

            # For greeting, we don't need to extract metadata from Gemini response
            # Just set basic metadata manually
            metadata = {"stage": "greeting", "intent": "initial_greeting"}
            session_manager.update_session({"last_intent": "initial_greeting"})
            customer_manager.update_session_in_comprehensive_data(customer_id, conversation_id, {"last_intent": "initial_greeting"})

            session_manager.add_to_chat_history(None, bot_response)
            session_manager.save_session()

        # === Main Conversation Loop ===
        conversation_ended = False
        while not conversation_ended:
            user_input = input(f"{customer_name} says: ")
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'end']:
                print("📞 Ending conversation...")
                customer_manager.end_conversation(customer_id, conversation_id, "user_terminated")
                break
            
            current_stage = session_manager.get_current_stage()
            
            if user_input.strip():  # Only process if user provided input
                # Debug: Show current state if debug mode enabled
                if config.is_debug_mode():
                    print(f"\n🔍 DEBUG: Current stage: {current_stage}")
                    current_branch = branches_manager.read_branch(current_stage)
                    if current_branch:
                        expected_types = list(current_branch.get("expected_user_responses", {}).keys())
                        print(f"🔍 DEBUG: Expected response types: {expected_types}")
                
                # Process conversation turn with interruption handling
                bot_response, metadata, conversation_continues = conversation_controller.process_conversation_turn(
                    user_input, current_stage, user_data, session_data
                )
                
                print(bot_response)
                
                # Add to comprehensive data system
                customer_manager.add_chat_message(customer_id, conversation_id, user_input, bot_response, metadata)
            
            else:
                # Empty input - prompt user to respond instead of calling Gemini
                print("Please provide a response to continue the conversation.")
                continue  # Skip this iteration and ask for input again

            # Update session data based on metadata
            if "update" in metadata:
                session_manager.update_session(metadata["update"])
                customer_manager.update_session_in_comprehensive_data(customer_id, conversation_id, metadata["update"])
            if "intent" in metadata:
                session_manager.update_session({"last_intent": metadata["intent"]})
                customer_manager.update_session_in_comprehensive_data(customer_id, conversation_id, {"last_intent": metadata["intent"]})

            session_manager.add_to_chat_history(user_input, bot_response)
            
            if config.should_auto_save():
                session_manager.save_session()

            # Check if we've transitioned to a closure branch and need to display its final message
            current_stage_after_update = session_manager.get_current_stage()
            closure_branches = {"closure", "payment_success_closure", "complaint_resolution_closure", "schedule_callback"}
            
            if (current_stage_after_update in closure_branches and 
                current_stage_after_update != current_stage):  # We just transitioned to a closure branch
                
                # Get the closure branch's bot_prompt and display it
                closure_branch = branches_manager.read_branch(current_stage_after_update)
                if closure_branch and "bot_prompt" in closure_branch:
                    final_message = closure_branch["bot_prompt"]
                    # Replace any placeholders with user data
                    for key, value in user_data.items():
                        final_message = final_message.replace(f"{{{key}}}", str(value))
                    
                    print(final_message)
                    
                    # Add this final message to chat history and comprehensive data
                    session_manager.add_to_chat_history(None, final_message)
                    customer_manager.add_chat_message(customer_id, conversation_id, None, final_message, 
                                                   {"stage": current_stage_after_update, "final_closure_message": True})

            if session_manager.is_conversation_complete():
                print(f"✅ Conversation with {customer_name} completed.")
                customer_manager.end_conversation(customer_id, conversation_id, "successful")
                conversation_ended = True
                
                # Show pending suggestions summary
                pending_suggestions = branches_manager.get_pending_suggestions()
                pending_ops = pending_suggestions.get("pending_operations", [])
                if pending_ops:
                    print(f"\n💡 Veena has made {len(pending_ops)} suggestions to improve future conversations.")
                    print("Use 'apply_suggestions.py' to review and apply these suggestions to branches.json")
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Conversation with {customer_name} interrupted by user.")
        customer_manager.end_conversation(customer_id, conversation_id, "interrupted")
    
    except Exception as e:
        print(f"\n❌ Error during conversation with {customer_name}: {e}")
        customer_manager.end_conversation(customer_id, conversation_id, "error", {"error": str(e)})
    
    finally:
        # Clean up customer-specific session files
        customer_manager.cleanup_customer_session_files(customer_id)


def main():
    """Main function to run the agent with customer selection"""
    
    print("🤖 Welcome to BotBuddy Multi-Customer Agent!")
    
    while True:
        # Customer selection
        selected_customer = select_customer()
        
        if not selected_customer:
            print("👋 Goodbye!")
            break
        
        # Run conversation for selected customer
        run_conversation_for_customer(selected_customer)
        
        # Ask if user wants to call another customer
        another_call = input("\n📞 Do you want to call another customer? (y/n): ").strip().lower()
        if another_call not in ['y', 'yes']:
            print("👋 Thanks for using BotBuddy!")
            break


if __name__ == "__main__":
    main()
