"""
Enhanced Customer Manager with Comprehensive Data Integration
"""
from comprehensive_data_manager import ComprehensiveDataManager
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class EnhancedCustomerManager:
    """Enhanced customer manager using comprehensive data structure"""
    
    def __init__(self, data_file: str = "botbuddy_comprehensive_data.json"):
        self.data_manager = ComprehensiveDataManager(data_file)
        self.current_conversation_id = None
    
    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Get list of all customers"""
        return self.data_manager.get_all_customers()
    
    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get specific customer by ID"""
        customer_data = self.data_manager.get_customer_data(customer_id)
        if customer_data:
            # Flatten the customer structure for easier access
            customer = customer_data["profile"].copy()
            customer.update({
                "conversation_status": customer_data["status"]["conversation_status"],
                "priority": customer_data["status"]["priority"],
                "call_attempts": customer_data["status"]["call_attempts"],
                "next_call_scheduled": customer_data["status"]["next_call_scheduled"],
                "tags": customer_data["status"]["tags"],
                "notes": customer_data["status"]["notes"],
                "analytics": customer_data["analytics"]
            })
            return customer
            
        # Fallback to the old method if direct lookup fails
        customers = self.get_all_customers()
        for customer in customers:
            if customer["id"] == customer_id:
                return customer
        return None
    
    def get_customer_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get customer by name (case insensitive)"""
        customers = self.get_all_customers()
        for customer in customers:
            if customer["policy_holder_name"].lower() == name.lower():
                return customer
        return None
    
    def get_customer_for_conversation(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get customer data for starting conversation (by name, ID, or number)"""
        customers = self.get_all_customers()
        
        # Try to find by customer number (1, 2, 3...)
        try:
            customer_num = int(identifier)
            if 1 <= customer_num <= len(customers):
                return customers[customer_num - 1]
        except ValueError:
            pass
        
        # Try to find by customer ID
        customer = self.get_customer_by_id(identifier)
        if customer:
            return customer
        
        # Try to find by name
        customer = self.get_customer_by_name(identifier)
        if customer:
            return customer
        
        return None
    
    def display_customers_list(self) -> None:
        """Display formatted list of all customers"""
        customers = self.get_all_customers()
        
        print("\n" + "="*100)
        print("                                    CUSTOMER LIST")
        print("="*100)
        print(f"{'#':<3} {'Name':<20} {'Policy No.':<15} {'Status':<15} {'Outstanding':<12} {'Priority':<8} {'Conversations':<12}")
        print("-"*100)
        
        for i, customer in enumerate(customers, 1):
            name = customer["policy_holder_name"][:19]
            policy_no = customer["policy_number"]
            conv_status = customer["conversation_status"]
            outstanding = customer["outstanding_amount"]
            priority = customer["priority"]
            total_convs = customer["analytics"]["total_conversations"]
            
            # Status symbols
            status_symbol = {
                "pending": "⏳",
                "calling": "📞",
                "completed": "✅",
                "failed": "❌",
                "callback_scheduled": "📅"
            }.get(conv_status, "❓")
            
            priority_symbol = {
                "high": "🔴",
                "medium": "🟡", 
                "low": "🟢"
            }.get(priority, "⚪")
            
            print(f"{i:<3} {name:<20} {policy_no:<15} {status_symbol} {conv_status:<13} {outstanding:<12} {priority_symbol} {priority:<7} {total_convs:<12}")
        
        print("="*100)
        
        # Show comprehensive summary
        summary = self.data_manager.get_data_summary()
        print(f"Total Customers: {summary['total_customers']}")
        print(f"Total Conversations: {summary['total_conversations']}")
        print(f"Successful Conversations: {summary['successful_conversations']}")
        
        print("\nStatus Summary:")
        for status, count in summary['status_distribution'].items():
            symbol = {
                "pending": "⏳",
                "calling": "📞", 
                "completed": "✅",
                "failed": "❌",
                "callback_scheduled": "📅"
            }.get(status, "❓")
            print(f"  {symbol} {status.title()}: {count}")
        
        print("\nPriority Distribution:")
        for priority, count in summary['priority_distribution'].items():
            symbol = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            print(f"  {symbol} {priority.title()}: {count}")
        
        print("="*100)
    
    def start_conversation(self, customer_id: str) -> str:
        """Start a new conversation and return conversation ID"""
        conversation_data = {
            "start_time": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        if self.data_manager.add_conversation_record(customer_id, conversation_data):
            # Get the latest conversation ID
            conversations = self.data_manager.get_customer_conversations(customer_id)
            if conversations:
                self.current_conversation_id = conversations[-1]["conversation_id"]
                
                # Update customer status
                self.update_customer_status(customer_id, "calling", {
                    "call_attempts": self.get_customer_by_id(customer_id)["call_attempts"] + 1,
                    "last_call_attempt": datetime.now().isoformat()
                })
                
                return self.current_conversation_id
        
        return None
    
    def end_conversation(self, customer_id: str, conversation_id: str, outcome: str, additional_data: Dict[str, Any] = None) -> bool:
        """End a conversation with outcome"""
        end_data = {
            "end_time": datetime.now().isoformat(),
            "status": "completed",
            "outcome": outcome
        }
        
        if additional_data:
            end_data.update(additional_data)
        
        # Get the conversation to check for callback information and calculate duration
        conversation_data = None
        conversations = self.data_manager.get_customer_conversations(customer_id)
        for conv in conversations:
            if conv["conversation_id"] == conversation_id:
                conversation_data = conv
                start_time = datetime.fromisoformat(conv["start_time"])
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                end_data["duration_seconds"] = duration
                break
        
        # Add callback data to the conversation record if applicable
        if conversation_data:
            session_data = conversation_data.get("session_data", {})
            if session_data.get("callback_scheduled") and "next_call_scheduled" in session_data:
                # Store the interrupted stage to resume from later (if not already set)
                if "interrupted_stage" not in session_data and "conversation_stage" in session_data:
                    session_data["interrupted_stage"] = session_data["conversation_stage"]
                
                # Update the next call scheduled time for customer status
                end_data["next_call_scheduled"] = session_data.get("next_call_scheduled")
        
        success = self.data_manager.update_conversation_record(customer_id, conversation_id, end_data)
        
        if success:
            # Update customer status based on outcome
            if outcome == "successful":
                new_status = "completed"
            elif outcome in ["callback_requested", "user_terminated"] and conversation_data and conversation_data.get("session_data", {}).get("callback_scheduled"):
                new_status = "callback_scheduled"
                # Extract callback time from session data
                next_call_time = conversation_data.get("session_data", {}).get("next_call_scheduled")
                self.update_customer_status(customer_id, new_status, {
                    "next_call_scheduled": next_call_time
                })
                return True  # Return early as we've already updated status with additional data
            else:
                new_status = "failed"
            
            self.update_customer_status(customer_id, new_status, {
                "last_successful_contact": datetime.now().isoformat() if outcome == "successful" else None
            })
        
        self.current_conversation_id = None
        return success
    
    def add_chat_message(self, customer_id: str, conversation_id: str, user_input: str, bot_response: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a chat message to the current conversation"""
        return self.data_manager.add_chat_message(customer_id, conversation_id, user_input, bot_response, metadata)
    
    def update_customer_status(self, customer_id: str, status: str, additional_data: Dict[str, Any] = None) -> bool:
        """Update customer status"""
        status_updates = {"conversation_status": status}
        
        if additional_data:
            status_updates.update(additional_data)
        
        return self.data_manager.update_customer_status(customer_id, status_updates)
    
    def update_customer_profile(self, customer_id: str, profile_updates: Dict[str, Any]) -> bool:
        """Update customer profile information"""
        return self.data_manager.update_customer_profile(customer_id, profile_updates)
    
    def add_customer_note(self, customer_id: str, note: str) -> bool:
        """Add a note to customer record"""
        customer = self.get_customer_by_id(customer_id)
        if customer:
            existing_notes = customer.get("notes", "")
            new_note = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}"
            updated_notes = f"{existing_notes}\n{new_note}" if existing_notes else new_note
            
            return self.update_customer_status(customer_id, None, {"notes": updated_notes})
        
        return False
    
    def add_customer_tag(self, customer_id: str, tag: str) -> bool:
        """Add a tag to customer"""
        customer = self.get_customer_by_id(customer_id)
        if customer:
            tags = customer.get("tags", [])
            if tag not in tags:
                tags.append(tag)
                return self.update_customer_status(customer_id, None, {"tags": tags})
        
        return False
    
    def remove_customer_tag(self, customer_id: str, tag: str) -> bool:
        """Remove a tag from customer"""
        customer = self.get_customer_by_id(customer_id)
        if customer:
            tags = customer.get("tags", [])
            if tag in tags:
                tags.remove(tag)
                return self.update_customer_status(customer_id, None, {"tags": tags})
        
        return False
    
    def get_customer_conversations_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get full conversation history for a customer"""
        return self.data_manager.get_customer_conversations(customer_id)
    
    def search_customers(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search customers based on criteria"""
        return self.data_manager.search_customers(search_criteria)
    
    def add_new_customer(self, customer_data: Dict[str, Any]) -> str:
        """Add a new customer"""
        return self.data_manager.add_new_customer(customer_data)
    
    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer"""
        return self.data_manager.delete_customer(customer_id)
    
    def export_customer_data(self, customer_id: str, file_path: str) -> bool:
        """Export customer data to file"""
        return self.data_manager.export_customer_data(customer_id, file_path)
    
    def backup_all_data(self, backup_suffix: str = None) -> bool:
        """Backup all customer data"""
        return self.data_manager.backup_all_data(backup_suffix)
    
    def create_session_files_for_customer(self, customer: Dict[str, Any]) -> tuple[str, str]:
        """Create customer-specific session files (for backward compatibility)"""
        customer_id = customer["id"]
        
        # Create user_data file for this customer
        user_data_file = f"user_data_{customer_id}.json"
        session_data_file = f"session_data_{customer_id}.json"
        
        # Extract user data (policy info)
        user_data = {k: v for k, v in customer.items() 
                    if k not in ["id", "phone", "conversation_status", "last_call_attempt", "call_attempts", "priority", "analytics", "tags", "notes"]}
        
        # Save user data file
        import json
        with open(user_data_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False)
        
        # Check if this is a callback and we need to restore previous session state
        session_data = self._get_session_data_for_callback(customer_id) or {
            "conversation_stage": "greeting",
            "language_preference": "English",
            "user_agreed_to_pay": None,
            "callback_scheduled": False,
            "chat_history": [],
            "last_intent": None,
            "customer_id": customer_id,
            "comprehensive_conversation_id": self.current_conversation_id,
            "is_callback": False
        }
        
        # Save session data file
        with open(session_data_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        
        return user_data_file, session_data_file
        
    def _get_session_data_for_callback(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Check if this customer has a pending callback and prepare appropriate session data"""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return None
            
        # Check if customer has callback_scheduled status
        if customer.get("conversation_status") == "callback_scheduled" and customer.get("next_call_scheduled"):
            # Find the most recent conversation with callback_scheduled = True
            conversations = self.data_manager.get_customer_conversations(customer_id)
            for conv in reversed(conversations):
                session_data = conv.get("session_data", {})
                if session_data.get("callback_scheduled") and session_data.get("conversation_stage"):
                    # Create new session data based on the callback information
                    callback_session = session_data.copy()
                    # Mark this as a callback continuation
                    callback_session["is_callback"] = True
                    callback_session["previous_conversation_id"] = conv.get("conversation_id")
                    callback_session["continued_from_callback"] = True
                    callback_session["callback_time"] = customer.get("next_call_scheduled")
                    callback_session["comprehensive_conversation_id"] = self.current_conversation_id
                    
                    # We want to start from where we left off, not the closure stage
                    if callback_session.get("conversation_stage") == "closure":
                        # If the conversation ended at closure, check if there was an interrupted stage
                        # or use a default fallback stage
                        callback_session["conversation_stage"] = callback_session.get("interrupted_stage", "policy_confirmation")
                    
                    return callback_session
        
        return None
    
    def cleanup_customer_session_files(self, customer_id: str) -> None:
        """Clean up customer-specific session files"""
        import os
        files_to_remove = [
            f"user_data_{customer_id}.json",
            f"session_data_{customer_id}.json"
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Could not remove {file_path}: {e}")
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        return self.data_manager.get_data_summary()
    
    def update_session_in_comprehensive_data(self, customer_id: str, conversation_id: str, session_updates: Dict[str, Any]) -> bool:
        """Update session data in comprehensive structure"""
        conversations = self.data_manager.get_customer_conversations(customer_id)
        for conv in conversations:
            if conv["conversation_id"] == conversation_id:
                conv["session_data"].update(session_updates)
                return self.data_manager._save_data()
        return False
