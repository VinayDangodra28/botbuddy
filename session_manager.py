"""
Session Management Module
Handles session data loading, saving, and user data management
"""
import json
from typing import Dict, Any, Optional
import os


class SessionManager:
    """Manages session data and user data for the conversation agent"""
    
    def __init__(self, user_data_file: str = "user_data.json", session_data_file: str = "session_data.json"):
        self.user_data_file = user_data_file
        self.session_data_file = session_data_file
        self.user_data = self._load_user_data()
        self.session_data = self._load_session_data()
    
    def _load_user_data(self) -> Dict[str, Any]:
        """Load static user data"""
        try:
            with open(self.user_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {self.user_data_file} not found, using empty user data")
            return {}
    
    def _load_session_data(self) -> Dict[str, Any]:
        """Load or initialize session data"""
        try:
            with open(self.session_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "conversation_stage": "greeting",
                "language_preference": "English",
                "user_agreed_to_pay": None,
                "callback_scheduled": False,
                "chat_history": [],
                "last_intent": None
            }
    
    def save_session(self) -> bool:
        """Save session data to file"""
        try:
            with open(self.session_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def update_session(self, updates: Dict[str, Any]) -> None:
        """Update session data with new values"""
        for key, value in updates.items():
            self.session_data[key] = value
    
    def add_to_chat_history(self, user_input: Optional[str], bot_response: str) -> None:
        """Add conversation turn to chat history"""
        self.session_data.setdefault("chat_history", []).append({
            "user": user_input,
            "veena": bot_response
        })
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get current session data"""
        return self.session_data
    
    def get_user_data(self) -> Dict[str, Any]:
        """Get user data"""
        return self.user_data
    
    def is_conversation_complete(self) -> bool:
        """Check if conversation is in any closure stage"""
        current_stage = self.session_data.get("conversation_stage", "greeting")
        closure_branches = {
            "closure", 
            "payment_success_closure", 
            "complaint_resolution_closure", 
            "schedule_callback"
        }
        return current_stage in closure_branches
    
    def get_current_stage(self) -> str:
        """Get current conversation stage"""
        return self.session_data.get("conversation_stage", "greeting")
    
    def backup_session(self, backup_suffix: str = "_backup") -> bool:
        """Create a backup of current session data"""
        try:
            backup_filename = self.session_data_file.replace('.json', f'{backup_suffix}.json')
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error creating session backup: {e}")
            return False
    
    def reset_session(self) -> None:
        """Reset session data to initial state"""
        self.session_data = {
            "conversation_stage": "greeting",
            "language_preference": "English", 
            "user_agreed_to_pay": None,
            "callback_scheduled": False,
            "chat_history": [],
            "last_intent": None
        }
