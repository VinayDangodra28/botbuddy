"""
Comprehensive Data Manager
Manages all customer data, sessions, conversations, and analytics in a single JSON structure
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid


class ComprehensiveDataManager:
    """Manages all BotBuddy data in a unified JSON structure"""
    
    def __init__(self, data_file: str = "botbuddy_comprehensive_data.json"):
        self.data_file = data_file
        self.data = self._load_comprehensive_data()
    
    def _load_comprehensive_data(self) -> Dict[str, Any]:
        """Load comprehensive data from file or create default structure"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_structure()
    
    def _create_default_structure(self) -> Dict[str, Any]:
        """Create default comprehensive data structure"""
        default_data = {
            "metadata": {
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_customers": 0,
                "total_conversations": 0,
                "total_successful_conversations": 0,
                "system_settings": {
                    "auto_save": True,
                    "debug_mode": False,
                    "default_language": "English",
                    "session_timeout_minutes": 30
                }
            },
            "customers": {
                "customer_001": {
                    "profile": {
                        "id": "customer_001",
                        "policy_holder_name": "Pratik Jadhav",
                        "policy_number": "VE12345678",
                        "product_name": "ValuEnable Shield Plan",
                        "grace_period": "30 days",
                        "policy_status": "Discontinuance",
                        "policy_bond": "Not available",
                        "policy_start_date": "2022-06-12",
                        "total_premium_paid": "₹50,000",
                        "premium_due_date": "2025-06-12",
                        "outstanding_amount": "₹10,000",
                        "sum_assured": "₹5,00,000",
                        "fund_value": "₹65,000",
                        "phone": "+91-9876543210",
                        "email": "pratik.jadhav@email.com",
                        "address": "Mumbai, Maharashtra",
                        "created_date": "2022-06-12",
                        "last_updated": datetime.now().isoformat()
                    },
                    "status": {
                        "conversation_status": "pending",
                        "priority": "high",
                        "call_attempts": 0,
                        "last_call_attempt": None,
                        "next_call_scheduled": None,
                        "tags": ["high_value", "lapsed_policy"],
                        "notes": "Policy in discontinuance state, requires immediate attention"
                    },
                    "conversations": [],
                    "analytics": {
                        "total_conversations": 0,
                        "successful_conversations": 0,
                        "failed_conversations": 0,
                        "callback_requests": 0,
                        "payment_promises": 0,
                        "average_conversation_duration": 0,
                        "last_successful_contact": None,
                        "conversion_rate": 0.0
                    }
                },
                "customer_002": {
                    "profile": {
                        "id": "customer_002",
                        "policy_holder_name": "Rajesh Kumar",
                        "policy_number": "VE87654321",
                        "product_name": "SecureLife Plus",
                        "grace_period": "45 days",
                        "policy_status": "Lapsed",
                        "policy_bond": "Available",
                        "policy_start_date": "2021-03-15",
                        "total_premium_paid": "₹75,000",
                        "premium_due_date": "2025-03-15",
                        "outstanding_amount": "₹15,000",
                        "sum_assured": "₹8,00,000",
                        "fund_value": "₹90,000",
                        "phone": "+91-9876543211",
                        "email": "rajesh.kumar@email.com",
                        "address": "Delhi, India",
                        "created_date": "2021-03-15",
                        "last_updated": datetime.now().isoformat()
                    },
                    "status": {
                        "conversation_status": "pending",
                        "priority": "medium",
                        "call_attempts": 0,
                        "last_call_attempt": None,
                        "next_call_scheduled": None,
                        "tags": ["medium_value", "lapsed_policy"],
                        "notes": "Policy lapsed, potential for revival"
                    },
                    "conversations": [],
                    "analytics": {
                        "total_conversations": 0,
                        "successful_conversations": 0,
                        "failed_conversations": 0,
                        "callback_requests": 0,
                        "payment_promises": 0,
                        "average_conversation_duration": 0,
                        "last_successful_contact": None,
                        "conversion_rate": 0.0
                    }
                },
                "customer_003": {
                    "profile": {
                        "id": "customer_003",
                        "policy_holder_name": "Priya Sharma",
                        "policy_number": "VE11223344",
                        "product_name": "WealthGrow Plan",
                        "grace_period": "60 days",
                        "policy_status": "Revival Pending",
                        "policy_bond": "Not available",
                        "policy_start_date": "2020-08-20",
                        "total_premium_paid": "₹1,20,000",
                        "premium_due_date": "2025-08-20",
                        "outstanding_amount": "₹25,000",
                        "sum_assured": "₹12,00,000",
                        "fund_value": "₹1,40,000",
                        "phone": "+91-9876543212",
                        "email": "priya.sharma@email.com",
                        "address": "Bangalore, Karnataka",
                        "created_date": "2020-08-20",
                        "last_updated": datetime.now().isoformat()
                    },
                    "status": {
                        "conversation_status": "pending",
                        "priority": "low",
                        "call_attempts": 0,
                        "last_call_attempt": None,
                        "next_call_scheduled": None,
                        "tags": ["high_value", "revival_pending"],
                        "notes": "High value customer, revival in progress"
                    },
                    "conversations": [],
                    "analytics": {
                        "total_conversations": 0,
                        "successful_conversations": 0,
                        "failed_conversations": 0,
                        "callback_requests": 0,
                        "payment_promises": 0,
                        "average_conversation_duration": 0,
                        "last_successful_contact": None,
                        "conversion_rate": 0.0
                    }
                }
            },
            "system_analytics": {
                "daily_stats": {},
                "monthly_stats": {},
                "agent_performance": {
                    "total_calls_made": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "callback_requests": 0,
                    "payment_commitments": 0,
                    "average_call_duration": 0,
                    "success_rate": 0.0
                },
                "conversation_flows": {
                    "most_common_paths": [],
                    "interruption_points": [],
                    "success_patterns": []
                }
            },
            "templates": {
                "conversation_templates": {},
                "response_templates": {},
                "email_templates": {}
            },
            "settings": {
                "business_rules": {
                    "max_call_attempts": 3,
                    "callback_wait_hours": 24,
                    "priority_escalation_days": 7,
                    "auto_reschedule": True
                },
                "ai_settings": {
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "model_version": "gemini-pro"
                }
            }
        }
        
        # Save the default structure
        self._save_data(default_data)
        return default_data
    
    def _save_data(self, data: Dict[str, Any] = None) -> bool:
        """Save comprehensive data to file"""
        try:
            data_to_save = data or self.data
            data_to_save["metadata"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving comprehensive data: {e}")
            return False
    
    def get_customer_data(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get complete customer data"""
        return self.data["customers"].get(customer_id)
    
    def update_customer_profile(self, customer_id: str, profile_updates: Dict[str, Any]) -> bool:
        """Update customer profile information"""
        if customer_id not in self.data["customers"]:
            return False
        
        self.data["customers"][customer_id]["profile"].update(profile_updates)
        self.data["customers"][customer_id]["profile"]["last_updated"] = datetime.now().isoformat()
        return self._save_data()
    
    def update_customer_status(self, customer_id: str, status_updates: Dict[str, Any]) -> bool:
        """Update customer status information"""
        if customer_id not in self.data["customers"]:
            return False
        
        self.data["customers"][customer_id]["status"].update(status_updates)
        return self._save_data()
    
    def add_conversation_record(self, customer_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Add a new conversation record"""
        if customer_id not in self.data["customers"]:
            return False
        
        conversation_record = {
            "conversation_id": str(uuid.uuid4()),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "status": "in_progress",
            "outcome": None,
            "session_data": {
                "conversation_stage": "greeting",
                "language_preference": "English",
                "user_agreed_to_pay": None,
                "callback_scheduled": False,
                "chat_history": [],
                "last_intent": None
            },
            "chat_history": [],
            "metadata": {
                "interruptions": 0,
                "branch_changes": [],
                "ai_suggestions": [],
                "quality_score": None
            }
        }
        
        conversation_record.update(conversation_data)
        self.data["customers"][customer_id]["conversations"].append(conversation_record)
        
        # Update analytics
        self.data["customers"][customer_id]["analytics"]["total_conversations"] += 1
        
        return self._save_data()
    
    def update_conversation_record(self, customer_id: str, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing conversation record"""
        if customer_id not in self.data["customers"]:
            return False
        
        conversations = self.data["customers"][customer_id]["conversations"]
        for conversation in conversations:
            if conversation["conversation_id"] == conversation_id:
                conversation.update(updates)
                
                # If conversation is ending, update analytics
                if updates.get("status") == "completed":
                    if updates.get("outcome") == "successful":
                        self.data["customers"][customer_id]["analytics"]["successful_conversations"] += 1
                    else:
                        self.data["customers"][customer_id]["analytics"]["failed_conversations"] += 1
                
                return self._save_data()
        
        return False
    
    def add_chat_message(self, customer_id: str, conversation_id: str, user_input: str, bot_response: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a chat message to conversation history"""
        if customer_id not in self.data["customers"]:
            return False
        
        conversations = self.data["customers"][customer_id]["conversations"]
        for conversation in conversations:
            if conversation["conversation_id"] == conversation_id:
                chat_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user": user_input,
                    "bot": bot_response,
                    "metadata": metadata or {}
                }
                
                conversation["chat_history"].append(chat_entry)
                conversation["session_data"]["chat_history"].append({
                    "user": user_input,
                    "veena": bot_response
                })
                
                return self._save_data()
        
        return False
    
    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Get list of all customers with combined data"""
        customers = []
        for customer_id, customer_data in self.data["customers"].items():
            combined_customer = {
                "id": customer_id,
                **customer_data["profile"],
                **customer_data["status"],
                "analytics": customer_data["analytics"]
            }
            customers.append(combined_customer)
        return customers
    
    def add_new_customer(self, customer_data: Dict[str, Any]) -> str:
        """Add a new customer with complete structure"""
        # Generate customer ID
        existing_count = len(self.data["customers"])
        customer_id = f"customer_{existing_count + 1:03d}"
        
        # Create complete customer structure
        new_customer = {
            "profile": {
                "id": customer_id,
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                **customer_data
            },
            "status": {
                "conversation_status": "pending",
                "priority": "medium",
                "call_attempts": 0,
                "last_call_attempt": None,
                "next_call_scheduled": None,
                "tags": [],
                "notes": ""
            },
            "conversations": [],
            "analytics": {
                "total_conversations": 0,
                "successful_conversations": 0,
                "failed_conversations": 0,
                "callback_requests": 0,
                "payment_promises": 0,
                "average_conversation_duration": 0,
                "last_successful_contact": None,
                "conversion_rate": 0.0
            }
        }
        
        self.data["customers"][customer_id] = new_customer
        self.data["metadata"]["total_customers"] += 1
        
        self._save_data()
        return customer_id
    
    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer and all associated data"""
        if customer_id in self.data["customers"]:
            del self.data["customers"][customer_id]
            self.data["metadata"]["total_customers"] -= 1
            return self._save_data()
        return False
    
    def get_customer_conversations(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a customer"""
        if customer_id in self.data["customers"]:
            return self.data["customers"][customer_id]["conversations"]
        return []
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics"""
        return self.data["system_analytics"]
    
    def update_system_analytics(self, analytics_updates: Dict[str, Any]) -> bool:
        """Update system analytics"""
        self.data["system_analytics"].update(analytics_updates)
        return self._save_data()
    
    def export_customer_data(self, customer_id: str, file_path: str) -> bool:
        """Export specific customer data to file"""
        if customer_id not in self.data["customers"]:
            return False
        
        try:
            customer_data = {
                "customer_id": customer_id,
                "export_date": datetime.now().isoformat(),
                "data": self.data["customers"][customer_id]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(customer_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting customer data: {e}")
            return False
    
    def import_customer_data(self, file_path: str) -> bool:
        """Import customer data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if "customer_id" in import_data and "data" in import_data:
                customer_id = import_data["customer_id"]
                self.data["customers"][customer_id] = import_data["data"]
                return self._save_data()
            
            return False
        except Exception as e:
            print(f"Error importing customer data: {e}")
            return False
    
    def backup_all_data(self, backup_suffix: str = None) -> bool:
        """Create a backup of all data"""
        if not backup_suffix:
            backup_suffix = datetime.now().strftime("_%Y%m%d_%H%M%S")
        
        backup_file = self.data_file.replace('.json', f'{backup_suffix}.json')
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def search_customers(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search customers based on criteria"""
        results = []
        for customer_id, customer_data in self.data["customers"].items():
            match = True
            
            for key, value in search_criteria.items():
                if key in customer_data["profile"]:
                    if str(value).lower() not in str(customer_data["profile"][key]).lower():
                        match = False
                        break
                elif key in customer_data["status"]:
                    if str(value).lower() not in str(customer_data["status"][key]).lower():
                        match = False
                        break
            
            if match:
                combined_customer = {
                    "id": customer_id,
                    **customer_data["profile"],
                    **customer_data["status"]
                }
                results.append(combined_customer)
        
        return results
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get comprehensive data summary"""
        customers = self.get_all_customers()
        
        status_counts = {}
        priority_counts = {}
        
        for customer in customers:
            status = customer.get("conversation_status", "unknown")
            priority = customer.get("priority", "unknown")
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "total_customers": len(customers),
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "total_conversations": sum(c["analytics"]["total_conversations"] for c in self.data["customers"].values()),
            "successful_conversations": sum(c["analytics"]["successful_conversations"] for c in self.data["customers"].values()),
            "last_updated": self.data["metadata"]["last_updated"]
        }
