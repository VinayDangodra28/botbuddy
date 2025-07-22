"""
Data Reset Utility
Resets BotBuddy comprehensive data to clean state
"""
import json
import shutil
import os
from datetime import datetime
from typing import Dict, Any


class DataResetUtility:
    """Utility for resetting BotBuddy data to clean state"""
    
    def __init__(self):
        self.main_data_file = "botbuddy_comprehensive_data.json"
        self.template_file = "botbuddy_data_template.json"
        self.backup_dir = "data_backups"
    
    def create_backup_before_reset(self) -> str:
        """Create a backup of current data before reset"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_before_reset_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            if os.path.exists(self.main_data_file):
                shutil.copy2(self.main_data_file, backup_path)
                return backup_path
            else:
                print("⚠️ No existing data file found to backup.")
                return None
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return None
    
    def reset_data_from_template(self) -> bool:
        """Reset main data file using template"""
        try:
            if not os.path.exists(self.template_file):
                print(f"❌ Template file '{self.template_file}' not found!")
                return False
            
            # Load template data
            with open(self.template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Update timestamps
            current_time = datetime.now().isoformat()
            template_data["metadata"]["created"] = current_time
            template_data["metadata"]["last_updated"] = current_time
            
            # Update customer profile timestamps
            for customer_id, customer_data in template_data["customers"].items():
                template_data["customers"][customer_id]["profile"]["last_updated"] = current_time
            
            # Save as main data file
            with open(self.main_data_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=4, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Error resetting data: {e}")
            return False
    
    def clean_session_files(self) -> int:
        """Clean up temporary session files"""
        cleaned_count = 0
        
        # Pattern for session files
        session_patterns = [
            "user_data_customer_*.json",
            "session_data_customer_*.json"
        ]
        
        try:
            for pattern in session_patterns:
                # Convert pattern to regex-like matching
                import glob
                files = glob.glob(pattern)
                for file in files:
                    try:
                        os.remove(file)
                        cleaned_count += 1
                        print(f"🧹 Removed: {file}")
                    except Exception as e:
                        print(f"⚠️ Could not remove {file}: {e}")
        
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
        
        return cleaned_count
    
    def display_current_status(self) -> Dict[str, Any]:
        """Display current data status"""
        try:
            if not os.path.exists(self.main_data_file):
                return {"status": "No data file exists", "customers": 0, "conversations": 0}
            
            with open(self.main_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_customers = len(data.get("customers", {}))
            total_conversations = 0
            total_successful = 0
            total_failed = 0
            
            for customer_id, customer_data in data.get("customers", {}).items():
                conversations = customer_data.get("conversations", [])
                total_conversations += len(conversations)
                
                analytics = customer_data.get("analytics", {})
                total_successful += analytics.get("successful_conversations", 0)
                total_failed += analytics.get("failed_conversations", 0)
            
            return {
                "status": "Active",
                "customers": total_customers,
                "total_conversations": total_conversations,
                "successful_conversations": total_successful,
                "failed_conversations": total_failed,
                "last_updated": data.get("metadata", {}).get("last_updated", "Unknown")
            }
            
        except Exception as e:
            return {"status": f"Error reading data: {e}", "customers": 0, "conversations": 0}
    
    def interactive_reset(self):
        """Interactive reset process"""
        print("\n" + "="*70)
        print("                    BOTBUDDY DATA RESET UTILITY")
        print("="*70)
        
        # Show current status
        status = self.display_current_status()
        print(f"\n📊 CURRENT STATUS:")
        print(f"   Status: {status['status']}")
        print(f"   Customers: {status['customers']}")
        print(f"   Total Conversations: {status['total_conversations']}")
        if 'successful_conversations' in status:
            print(f"   Successful: {status['successful_conversations']}")
            print(f"   Failed: {status['failed_conversations']}")
        if 'last_updated' in status:
            print(f"   Last Updated: {status['last_updated']}")
        
        print(f"\n⚠️ WARNING: This will reset ALL data including:")
        print(f"   • All customer conversation history")
        print(f"   • All analytics and performance data") 
        print(f"   • All session data and progress")
        print(f"   • System statistics and metrics")
        
        print(f"\n✅ What will be preserved:")
        print(f"   • Customer profile information")
        print(f"   • Customer tags and notes")
        print(f"   • System settings and configuration")
        
        confirm = input(f"\n❓ Do you want to proceed with reset? (type 'RESET' to confirm): ").strip()
        
        if confirm != 'RESET':
            print("❌ Reset cancelled.")
            return False
        
        print(f"\n🔄 Starting reset process...")
        
        # Step 1: Create backup
        print("📦 Creating backup...")
        backup_path = self.create_backup_before_reset()
        if backup_path:
            print(f"✅ Backup created: {backup_path}")
        
        # Step 2: Reset data
        print("🔄 Resetting data from template...")
        if self.reset_data_from_template():
            print("✅ Data reset successful!")
        else:
            print("❌ Data reset failed!")
            return False
        
        # Step 3: Clean session files
        print("🧹 Cleaning temporary files...")
        cleaned_count = self.clean_session_files()
        print(f"✅ Cleaned {cleaned_count} temporary files")
        
        # Step 4: Show new status
        print("\n📊 NEW STATUS:")
        new_status = self.display_current_status()
        print(f"   Status: {new_status['status']}")
        print(f"   Customers: {new_status['customers']}")
        print(f"   Total Conversations: {new_status['total_conversations']}")
        
        print(f"\n🎉 Reset completed successfully!")
        print(f"   • All conversation history cleared")
        print(f"   • All analytics reset to zero")
        print(f"   • Customer profiles preserved")
        print(f"   • System ready for fresh start")
        
        return True
    
    def quick_reset(self) -> bool:
        """Quick reset without interactive prompts"""
        backup_path = self.create_backup_before_reset()
        success = self.reset_data_from_template()
        self.clean_session_files()
        return success
    
    def list_backups(self):
        """List all available backups"""
        if not os.path.exists(self.backup_dir):
            print("📁 No backups directory found.")
            return
        
        backups = [f for f in os.listdir(self.backup_dir) if f.endswith('.json')]
        
        if not backups:
            print("📁 No backup files found.")
            return
        
        print(f"\n📁 AVAILABLE BACKUPS ({len(backups)} files):")
        print("="*60)
        
        for backup in sorted(backups, reverse=True):  # Most recent first
            backup_path = os.path.join(self.backup_dir, backup)
            try:
                stat = os.stat(backup_path)
                size_kb = stat.st_size / 1024
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # Try to read backup metadata
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    customers = len(data.get("customers", {}))
                    conversations = sum(len(c.get("conversations", [])) for c in data.get("customers", {}).values())
                    
                    print(f"📄 {backup}")
                    print(f"   Size: {size_kb:.1f} KB | Created: {mod_time}")
                    print(f"   Data: {customers} customers, {conversations} conversations")
                    print()
                
                except json.JSONDecodeError:
                    print(f"📄 {backup} (corrupted)")
                    print(f"   Size: {size_kb:.1f} KB | Created: {mod_time}")
                    print()
                
            except Exception as e:
                print(f"📄 {backup} (error reading: {e})")
    
    def restore_from_backup(self, backup_filename: str = None):
        """Restore data from a backup file"""
        if not backup_filename:
            self.list_backups()
            backup_filename = input("\nEnter backup filename to restore: ").strip()
        
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file '{backup_filename}' not found!")
            return False
        
        try:
            # Validate backup file
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Create backup of current data first
            current_backup = self.create_backup_before_reset()
            if current_backup:
                print(f"✅ Current data backed up to: {os.path.basename(current_backup)}")
            
            # Restore from backup
            shutil.copy2(backup_path, self.main_data_file)
            
            print(f"✅ Data restored from: {backup_filename}")
            
            # Show restored status
            status = self.display_current_status()
            print(f"\n📊 RESTORED STATUS:")
            print(f"   Customers: {status['customers']}")
            print(f"   Total Conversations: {status['total_conversations']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring from backup: {e}")
            return False


def main():
    """Main function to run the reset utility"""
    utility = DataResetUtility()
    
    while True:
        print("\n" + "="*50)
        print("        BOTBUDDY DATA RESET UTILITY")
        print("="*50)
        print("1. Show Current Status")
        print("2. Interactive Reset (Recommended)")
        print("3. Quick Reset (No prompts)")
        print("4. List Backups")
        print("5. Restore from Backup")
        print("6. Exit")
        print("="*50)
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == "1":
            status = utility.display_current_status()
            print(f"\n📊 CURRENT STATUS:")
            for key, value in status.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
        
        elif choice == "2":
            utility.interactive_reset()
        
        elif choice == "3":
            print("🔄 Performing quick reset...")
            if utility.quick_reset():
                print("✅ Quick reset completed!")
            else:
                print("❌ Quick reset failed!")
        
        elif choice == "4":
            utility.list_backups()
        
        elif choice == "5":
            utility.restore_from_backup()
        
        elif choice == "6":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice! Please select 1-6.")


if __name__ == "__main__":
    main()
