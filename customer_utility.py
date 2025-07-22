"""
Customer Management Utility
Standalone script for managing customers
"""
from customer_manager import CustomerManager
import json


def add_new_customer():
    """Add a new customer to the system"""
    print("\n" + "="*60)
    print("                    ADD NEW CUSTOMER")
    print("="*60)
    
    customer_data = {}
    
    # Required fields
    required_fields = {
        "policy_holder_name": "Policy Holder Name",
        "policy_number": "Policy Number",
        "product_name": "Product Name",
        "outstanding_amount": "Outstanding Amount (e.g., ₹10,000)",
        "phone": "Phone Number (e.g., +91-9876543210)"
    }
    
    for field, display_name in required_fields.items():
        value = input(f"{display_name}: ").strip()
        if not value:
            print(f"❌ {display_name} is required!")
            return
        customer_data[field] = value
    
    # Optional fields with defaults
    optional_fields = {
        "grace_period": ("Grace Period", "30 days"),
        "policy_status": ("Policy Status", "Active"),
        "policy_bond": ("Policy Bond", "Available"),
        "policy_start_date": ("Policy Start Date (YYYY-MM-DD)", "2024-01-01"),
        "total_premium_paid": ("Total Premium Paid", "₹0"),
        "premium_due_date": ("Premium Due Date (YYYY-MM-DD)", "2025-01-01"),
        "sum_assured": ("Sum Assured", "₹5,00,000"),
        "fund_value": ("Fund Value", "₹0"),
        "priority": ("Priority (high/medium/low)", "medium")
    }
    
    print("\n--- Optional Fields (Press Enter for default) ---")
    for field, (display_name, default_value) in optional_fields.items():
        value = input(f"{display_name} [{default_value}]: ").strip()
        customer_data[field] = value if value else default_value
    
    # Generate customer ID
    cm = CustomerManager()
    existing_customers = cm.get_all_customers()
    customer_id = f"customer_{len(existing_customers) + 1:03d}"
    
    customer_data.update({
        "id": customer_id,
        "conversation_status": "pending",
        "last_call_attempt": None,
        "call_attempts": 0
    })
    
    # Add to customers list
    customers_data = cm.customers_data
    customers_data["customers"].append(customer_data)
    
    if cm._save_customers_data(customers_data):
        print(f"\n✅ Customer '{customer_data['policy_holder_name']}' added successfully!")
        print(f"   Customer ID: {customer_id}")
    else:
        print("\n❌ Failed to add customer!")


def view_customer_details():
    """View detailed information of a specific customer"""
    cm = CustomerManager()
    
    print("\n" + "="*60)
    print("                 VIEW CUSTOMER DETAILS")
    print("="*60)
    
    # Show quick list first
    customers = cm.get_all_customers()
    print("Available customers:")
    for i, customer in enumerate(customers, 1):
        print(f"  {i}. {customer['policy_holder_name']} ({customer['policy_number']})")
    
    identifier = input("\nEnter customer number, name, or ID: ").strip()
    customer = cm.get_customer_for_conversation(identifier)
    
    if customer:
        print("\n" + "="*60)
        print(f"         CUSTOMER DETAILS - {customer['policy_holder_name'].upper()}")
        print("="*60)
        
        details = [
            ("Customer ID", customer.get("id")),
            ("Policy Holder Name", customer.get("policy_holder_name")),
            ("Policy Number", customer.get("policy_number")),
            ("Product Name", customer.get("product_name")),
            ("Phone", customer.get("phone")),
            ("Policy Status", customer.get("policy_status")),
            ("Outstanding Amount", customer.get("outstanding_amount")),
            ("Premium Due Date", customer.get("premium_due_date")),
            ("Sum Assured", customer.get("sum_assured")),
            ("Fund Value", customer.get("fund_value")),
            ("Conversation Status", customer.get("conversation_status")),
            ("Priority", customer.get("priority")),
            ("Call Attempts", customer.get("call_attempts")),
            ("Last Call Attempt", customer.get("last_call_attempt"))
        ]
        
        for label, value in details:
            print(f"{label:<20}: {value}")
        
        print("="*60)
    else:
        print(f"\n❌ Customer '{identifier}' not found!")


def update_customer_priority():
    """Update customer priority"""
    cm = CustomerManager()
    
    print("\n" + "="*60)
    print("               UPDATE CUSTOMER PRIORITY")
    print("="*60)
    
    # Show customers with current priority
    customers = cm.get_all_customers()
    for i, customer in enumerate(customers, 1):
        priority_symbol = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(customer.get("priority"), "⚪")
        print(f"  {i}. {customer['policy_holder_name']} - {priority_symbol} {customer.get('priority', 'unknown')}")
    
    identifier = input("\nEnter customer number, name, or ID: ").strip()
    customer = cm.get_customer_for_conversation(identifier)
    
    if customer:
        current_priority = customer.get("priority", "medium")
        print(f"\nCurrent priority: {current_priority}")
        print("Available priorities: high, medium, low")
        
        new_priority = input("Enter new priority: ").strip().lower()
        
        if new_priority in ["high", "medium", "low"]:
            if cm.update_customer_status(customer["id"], customer["conversation_status"], {"priority": new_priority}):
                print(f"✅ Priority updated to '{new_priority}' for {customer['policy_holder_name']}")
            else:
                print("❌ Failed to update priority!")
        else:
            print("❌ Invalid priority! Use: high, medium, or low")
    else:
        print(f"\n❌ Customer '{identifier}' not found!")


def main_menu():
    """Main menu for customer management"""
    cm = CustomerManager()
    
    while True:
        print("\n" + "="*60)
        print("                CUSTOMER MANAGEMENT UTILITY")
        print("="*60)
        print("1. View All Customers")
        print("2. View Customer Details")
        print("3. Add New Customer")
        print("4. Update Customer Priority")
        print("5. Reset All Customer Status to Pending")
        print("6. Export Customer Data")
        print("7. Exit")
        print("="*60)
        
        choice = input("Select option (1-7): ").strip()
        
        if choice == "1":
            cm.display_customers_list()
        
        elif choice == "2":
            view_customer_details()
        
        elif choice == "3":
            add_new_customer()
        
        elif choice == "4":
            update_customer_priority()
        
        elif choice == "5":
            customers = cm.get_all_customers()
            confirm = input(f"Reset status for all {len(customers)} customers to 'pending'? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                for customer in customers:
                    cm.update_customer_status(customer["id"], "pending", {"call_attempts": 0})
                print("✅ All customer statuses reset to 'pending'")
        
        elif choice == "6":
            export_file = "customers_export.json"
            try:
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(cm.customers_data, f, indent=4, ensure_ascii=False)
                print(f"✅ Customer data exported to {export_file}")
            except Exception as e:
                print(f"❌ Export failed: {e}")
        
        elif choice == "7":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice! Please select 1-7.")


if __name__ == "__main__":
    main_menu()
