#!/usr/bin/env python3
"""
Apply Suggestions Script - Manage and apply Veena's conversation flow suggestions
"""

import json
import sys
from branches_manager import BranchesManager

def main():
    """Main function to handle suggestion operations"""
    
    # Initialize branches manager
    manager = BranchesManager("branches.json", "suggestions.json")
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list" or command == "show":
        show_pending_suggestions(manager)
    elif command == "preview":
        preview_suggestions(manager)
    elif command == "apply":
        if len(sys.argv) > 2 and sys.argv[2] == "all":
            apply_all_suggestions(manager)
        elif len(sys.argv) > 2:
            try:
                indices = [int(x) for x in sys.argv[2:]]
                apply_specific_suggestions(manager, indices)
            except ValueError:
                print("❌ Error: Invalid operation indices. Please provide numbers.")
        else:
            interactive_apply(manager)
    elif command == "clear":
        clear_suggestions(manager)
    elif command == "backup":
        backup_branches(manager)
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

def show_help():
    """Display help information"""
    print("""
🤖 Veena's Suggestion Manager

Usage: python apply_suggestions.py <command> [options]

Commands:
  list/show     - Show all pending suggestions
  preview      - Preview what would happen if suggestions are applied
  apply all    - Apply all pending suggestions
  apply <ids>  - Apply specific suggestions by ID (e.g., apply 0 1 3)
  apply        - Interactive mode to choose which suggestions to apply
  clear        - Clear all pending suggestions without applying
  backup       - Create backup of current branches.json

Examples:
  python apply_suggestions.py list
  python apply_suggestions.py apply all
  python apply_suggestions.py apply 0 2 4
  python apply_suggestions.py preview
    """)

def show_pending_suggestions(manager):
    """Display all pending suggestions"""
    suggestions = manager.get_pending_suggestions()
    pending_ops = suggestions.get("pending_operations", [])
    
    if not pending_ops:
        print("📄 No pending suggestions from Veena")
        return
    
    print(f"📋 Veena has {len(pending_ops)} pending suggestions:")
    print("=" * 60)
    
    for i, operation in enumerate(pending_ops):
        op_type = operation.get("operation_type", "Unknown").upper()
        data = operation.get("data", {})
        branch_name = data.get("branch_name", "Unknown")
        timestamp = operation.get("timestamp", "Unknown")
        
        print(f"\n{i}: {op_type} '{branch_name}'")
        print(f"   Time: {timestamp[:19] if timestamp != 'Unknown' else 'Unknown'}")
        
        if op_type == "CREATE":
            branch_data = data.get("branch_data", {})
            intent = branch_data.get("intent", "N/A")
            prompt = branch_data.get("bot_prompt", "N/A")
            print(f"   Intent: {intent}")
            print(f"   Prompt: {prompt[:50]}...")
            
            called_when = data.get("called_when", [])
            if called_when:
                print(f"   Called when: {len(called_when)} condition(s)")
        
        elif op_type == "UPDATE":
            updates = []
            if "intent" in data:
                updates.append("intent")
            if "bot_prompt" in data:
                updates.append("bot_prompt")
            if "expected_user_responses" in data:
                updates.append("responses")
            print(f"   Updates: {', '.join(updates)}")
        
        elif op_type == "DELETE":
            print(f"   Action: Remove branch")

def preview_suggestions(manager):
    """Preview what would happen if suggestions are applied"""
    print("🔍 Previewing suggestion effects...")
    preview = manager.preview_suggestions_effect()
    
    if "message" in preview:
        print(f"📄 {preview['message']}")
        return
    
    print("\n📊 Preview Results:")
    
    if preview.get("creates"):
        print(f"✨ Would CREATE: {', '.join(preview['creates'])}")
    
    if preview.get("updates"):
        print(f"✏️ Would UPDATE: {', '.join(preview['updates'])}")
    
    if preview.get("deletes"):
        print(f"🗑️ Would DELETE: {', '.join(preview['deletes'])}")
    
    if preview.get("potential_conflicts"):
        print(f"⚠️ Potential conflicts:")
        for conflict in preview["potential_conflicts"]:
            print(f"   - {conflict}")

def apply_all_suggestions(manager):
    """Apply all pending suggestions"""
    suggestions = manager.get_pending_suggestions()
    pending_ops = suggestions.get("pending_operations", [])
    
    if not pending_ops:
        print("📄 No pending suggestions to apply")
        return
    
    print(f"🔄 Applying all {len(pending_ops)} suggestions...")
    
    result = manager.apply_suggestions(verbose=True)
    
    if result.get("success"):
        print(f"\n✅ Successfully applied {result.get('applied', 0)} suggestions!")
    else:
        print(f"\n⚠️ Applied {result.get('applied', 0)} suggestions with {result.get('failed', 0)} failures")
        
        if result.get("errors"):
            print("Errors encountered:")
            for error in result["errors"]:
                print(f"  - {error}")

def apply_specific_suggestions(manager, indices):
    """Apply specific suggestions by index"""
    suggestions = manager.get_pending_suggestions()
    pending_ops = suggestions.get("pending_operations", [])
    
    if not pending_ops:
        print("📄 No pending suggestions to apply")
        return
    
    # Validate indices
    invalid_indices = [i for i in indices if i < 0 or i >= len(pending_ops)]
    if invalid_indices:
        print(f"❌ Invalid indices: {invalid_indices}")
        print(f"Valid range: 0 to {len(pending_ops) - 1}")
        return
    
    print(f"🔄 Applying suggestions at indices: {indices}")
    
    result = manager.apply_suggestions(operation_indices=indices, verbose=True)
    
    if result.get("success"):
        print(f"\n✅ Successfully applied {result.get('applied', 0)} suggestions!")
    else:
        print(f"\n⚠️ Applied {result.get('applied', 0)} suggestions with {result.get('failed', 0)} failures")

def interactive_apply(manager):
    """Interactive mode to choose which suggestions to apply"""
    suggestions = manager.get_pending_suggestions()
    pending_ops = suggestions.get("pending_operations", [])
    
    if not pending_ops:
        print("📄 No pending suggestions to apply")
        return
    
    print("🎯 Interactive Suggestion Application")
    show_pending_suggestions(manager)
    
    print("\nOptions:")
    print("  'all' - Apply all suggestions")
    print("  '0,2,4' - Apply specific suggestions by index")
    print("  'quit' - Exit without applying")
    
    while True:
        choice = input("\nWhat would you like to do? ").strip().lower()
        
        if choice == "quit":
            print("👋 Exiting without applying suggestions")
            break
        elif choice == "all":
            apply_all_suggestions(manager)
            break
        else:
            try:
                # Parse comma-separated indices
                indices = [int(x.strip()) for x in choice.split(",")]
                apply_specific_suggestions(manager, indices)
                break
            except ValueError:
                print("❌ Invalid input. Please use 'all', specific indices like '0,2,4', or 'quit'")

def clear_suggestions(manager):
    """Clear all suggestions without applying them"""
    suggestions = manager.get_pending_suggestions()
    pending_ops = suggestions.get("pending_operations", [])
    
    if not pending_ops:
        print("📄 No pending suggestions to clear")
        return
    
    print(f"⚠️ This will delete {len(pending_ops)} pending suggestions without applying them.")
    confirm = input("Are you sure? (type 'yes' to confirm): ").strip().lower()
    
    if confirm == "yes":
        success = manager.clear_suggestions()
        if success:
            print("🗑️ All suggestions cleared successfully")
        else:
            print("❌ Error clearing suggestions")
    else:
        print("👍 Cancelled - suggestions preserved")

def backup_branches(manager):
    """Create a backup of the current branches.json"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"branches_backup_{timestamp}.json"
    
    success = manager.export_to_file(backup_file)
    if success:
        print(f"💾 Backup created: {backup_file}")
    else:
        print("❌ Error creating backup")

if __name__ == "__main__":
    main()
