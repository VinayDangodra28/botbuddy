"""
Quick Data Reset Script
Simple script to reset BotBuddy data with one command
"""
from data_reset_utility import DataResetUtility
import sys


def main():
    """Main function for quick reset"""
    utility = DataResetUtility()
    
    print("🔄 BotBuddy Data Reset")
    print("=" * 30)
    
    # Show current status
    status = utility.display_current_status()
    print(f"Current Status: {status['customers']} customers, {status['total_conversations']} conversations")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        # Force reset without confirmation
        print("⚡ Force reset mode - no confirmation required")
        success = utility.quick_reset()
    else:
        # Ask for confirmation
        confirm = input("Reset all conversation data? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            success = utility.quick_reset()
        else:
            print("❌ Reset cancelled")
            return
    
    if success:
        new_status = utility.display_current_status()
        print("✅ Reset completed successfully!")
        print(f"📊 New Status: {new_status['customers']} customers, {new_status['total_conversations']} conversations")
        print("💾 Backup created in data_backups/ folder")
    else:
        print("❌ Reset failed!")


if __name__ == "__main__":
    main()
