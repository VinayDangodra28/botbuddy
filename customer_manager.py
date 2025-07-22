"""
Customer Management Module
Handles multiple customers, their data, and conversation status
"""
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class CustomerManager:
    """Manages multiple customers and their conversation states"""
    
    def __init__(self, customers_file: str = "customers.json"):
        self.customers_file = customers_file
        self.customers_data = self._load_customers_data()
    
    def _load_customers_data(self) -> Dict[str, Any]:
        """Load customers data from file"""
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default customers file with sample data
            default_data = {
                "customers": [
                    {
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
                        "conversation_status": "pending",
                        "last_call_attempt": None,
                        "call_attempts": 0,
                        "priority": "high"
                    },
                    {
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
                        "conversation_status": "pending",
                        "last_call_attempt": None,
                        "call_attempts": 0,
                        "priority": "medium"
                    },
                    {
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
                        "conversation_status": "pending",
                        "last_call_attempt": None,
                        "call_attempts": 0,
                        "priority": "low"
                    }
                ]
            }
            self._save_customers_data(default_data)
            return default_data
    
    def _save_customers_data(self, data: Dict[str, Any]) -> bool:
        """Save customers data to file"""
        try:
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving customers data: {e}")
            return False
    
    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Get list of all customers"""
        return self.customers_data.get("customers", [])
    
    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get specific customer by ID"""
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
    
    def update_customer_status(self, customer_id: str, status: str, additional_data: Dict[str, Any] = None) -> bool:
        """Update customer conversation status"""
        customers = self.get_all_customers()
        for customer in customers:
            if customer["id"] == customer_id:
                customer["conversation_status"] = status
                customer["last_call_attempt"] = datetime.now().isoformat()
                
                if additional_data:
                    customer.update(additional_data)
                
                # Update call attempts
                if status == "calling":
                    customer["call_attempts"] = customer.get("call_attempts", 0) + 1
                
                self.customers_data["customers"] = customers
                return self._save_customers_data(self.customers_data)
        return False
    
    def display_customers_list(self) -> None:
        """Display formatted list of all customers"""
        customers = self.get_all_customers()
        
        print("\n" + "="*80)
        print("                          CUSTOMER LIST")
        print("="*80)
        print(f"{'#':<3} {'Name':<20} {'Policy No.':<15} {'Status':<15} {'Outstanding':<12} {'Priority':<8}")
        print("-"*80)
        
        for i, customer in enumerate(customers, 1):
            name = customer["policy_holder_name"][:19]  # Truncate if too long
            policy_no = customer["policy_number"]
            conv_status = customer["conversation_status"]
            outstanding = customer["outstanding_amount"]
            priority = customer["priority"]
            
            # Color coding for status
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
            
            print(f"{i:<3} {name:<20} {policy_no:<15} {status_symbol} {conv_status:<13} {outstanding:<12} {priority_symbol} {priority:<7}")
        
        print("="*80)
        print(f"Total Customers: {len(customers)}")
        
        # Show summary stats
        status_counts = {}
        for customer in customers:
            status = customer["conversation_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nStatus Summary:")
        for status, count in status_counts.items():
            symbol = {
                "pending": "⏳",
                "calling": "📞", 
                "completed": "✅",
                "failed": "❌",
                "callback_scheduled": "📅"
            }.get(status, "❓")
            print(f"  {symbol} {status.title()}: {count}")
        print("="*80)
    
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
    
    def create_session_files_for_customer(self, customer: Dict[str, Any]) -> tuple[str, str]:
        """Create customer-specific session files"""
        customer_id = customer["id"]
        
        # Create user_data file for this customer
        user_data_file = f"user_data_{customer_id}.json"
        session_data_file = f"session_data_{customer_id}.json"
        
        # Extract user data (policy info)
        user_data = {k: v for k, v in customer.items() 
                    if k not in ["id", "phone", "conversation_status", "last_call_attempt", "call_attempts", "priority"]}
        
        # Save user data file
        with open(user_data_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False)
        
        # Create fresh session data
        session_data = {
            "conversation_stage": "greeting",
            "language_preference": "English",
            "user_agreed_to_pay": None,
            "callback_scheduled": False,
            "chat_history": [],
            "last_intent": None,
            "customer_id": customer_id
        }
        
        # Save session data file
        with open(session_data_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        
        return user_data_file, session_data_file
    
    def cleanup_customer_session_files(self, customer_id: str) -> None:
        """Clean up customer-specific session files"""
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
