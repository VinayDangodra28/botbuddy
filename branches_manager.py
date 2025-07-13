import json
import os
import datetime
from typing import Dict, List, Any, Optional


class BranchesManager:
    """
    A class to manage CRUD operations for branches.json file.
    Handles conversation flow branches with intents, prompts, and user responses.
    """
    
    def __init__(self, json_file_path: str = "branches.json", suggestions_file_path: str = "suggestions.json"):
        """
        Initialize the BranchesManager with the path to the JSON files.
        
        Args:
            json_file_path (str): Path to the branches.json file
            suggestions_file_path (str): Path to the suggestions.json file
        """
        self.json_file_path = json_file_path
        self.suggestions_file_path = suggestions_file_path
        self.branches = self._load_branches()
        self.suggestions = self._load_suggestions()
    
    def _load_branches(self) -> Dict[str, Any]:
        """Load branches from the JSON file."""
        try:
            if os.path.exists(self.json_file_path):
                with open(self.json_file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                return {}
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading branches: {e}")
            return {}

    def _load_suggestions(self) -> Dict[str, Any]:
        """Load suggestions from the suggestions JSON file."""
        try:
            if os.path.exists(self.suggestions_file_path):
                with open(self.suggestions_file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                return {"pending_operations": [], "timestamp": None}
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading suggestions: {e}")
            return {"pending_operations": [], "timestamp": None}
    
    def _save_branches(self) -> bool:
        """Save branches to the JSON file."""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.branches, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving branches: {e}")
            return False

    def _save_suggestions(self) -> bool:
        """Save suggestions to the suggestions JSON file."""
        try:
            with open(self.suggestions_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.suggestions, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving suggestions: {e}")
            return False

    def _add_operation_to_suggestions(self, operation_type: str, operation_data: Dict[str, Any]) -> bool:
        """Add an operation to the suggestions file."""
        import datetime
        
        operation = {
            "operation_type": operation_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": operation_data
        }
        
        self.suggestions["pending_operations"].append(operation)
        self.suggestions["timestamp"] = datetime.datetime.now().isoformat()
        
        return self._save_suggestions()
    
    def create_branch(
        self,
        branch_name: str,
        intent: str,
        bot_prompt: str,
        expected_user_responses: Dict[str, Any],
        called_when: Optional[List[Dict[str, Any]]] = None,
        action: Optional[str] = None
    ) -> bool:
        """
        Create a new branch suggestion (saved to suggestions.json).
        
        Args:
            branch_name (str): Name of the branch (unique identifier)
            intent (str): Intent of this branch
            bot_prompt (str): The prompt that the bot will say
            expected_user_responses (Dict): Dictionary of expected user responses
            called_when (List[Dict], optional): List of previous intents that can lead to this branch
                Format: [{"previous_intent": "intent_name", "previous_response": "response_key", "response_of_previous_response": "response_value"}]
            action (str, optional): Action to perform (e.g., "END_CALL")
        
        Returns:
            bool: True if suggestion was created successfully, False otherwise
        """
        if branch_name in self.branches:
            print(f"Branch '{branch_name}' already exists. Use update_branch() to modify it.")
            return False
        
        # Create the new branch structure
        new_branch = {
            "intent": intent,
            "bot_prompt": bot_prompt,
            "expected_user_responses": expected_user_responses
        }
        
        # Add optional action if provided
        if action:
            new_branch["action"] = action
        
        # Add operation to suggestions instead of directly to branches
        operation_data = {
            "branch_name": branch_name,
            "branch_data": new_branch,
            "called_when": called_when
        }
        
        success = self._add_operation_to_suggestions("create", operation_data)
        if success:
            print(f"Branch creation suggestion for '{branch_name}' saved to suggestions.json")
        
        return success
    
    def read_branch(self, branch_name: str) -> Optional[Dict[str, Any]]:
        """
        Read a specific branch by name.
        
        Args:
            branch_name (str): Name of the branch to read
        
        Returns:
            Dict or None: Branch data if found, None otherwise
        """
        return self.branches.get(branch_name)
    
    def read_all_branches(self) -> Dict[str, Any]:
        """
        Read all branches.
        
        Returns:
            Dict: All branches data
        """
        return self.branches.copy()
    
    def update_branch(
        self,
        branch_name: str,
        intent: Optional[str] = None,
        bot_prompt: Optional[str] = None,
        expected_user_responses: Optional[Dict[str, Any]] = None,
        called_when: Optional[List[Dict[str, Any]]] = None,
        action: Optional[str] = None
    ) -> bool:
        """
        Update an existing branch by adding to suggestions.
        
        Args:
            branch_name (str): Name of the branch to update
            intent (str, optional): New intent
            bot_prompt (str, optional): New bot prompt
            expected_user_responses (Dict, optional): New expected user responses
            called_when (List[Dict], optional): New called_when configuration
            action (str, optional): New action
        
        Returns:
            bool: True if the suggestion was added successfully, False otherwise
        """
        if branch_name not in self.branches:
            print(f"Branch '{branch_name}' does not exist. Use create_branch() to create it.")
            return False
        
        # Prepare update data
        update_data = {"branch_name": branch_name}
        
        if intent is not None:
            update_data["intent"] = intent
        
        if bot_prompt is not None:
            update_data["bot_prompt"] = bot_prompt
        
        if expected_user_responses is not None:
            update_data["expected_user_responses"] = expected_user_responses
        
        if called_when is not None:
            update_data["called_when"] = called_when
        
        if action is not None:
            update_data["action"] = action
        
        # Add to suggestions
        return self._add_operation_to_suggestions("update", update_data)
    
    def delete_branch(self, branch_name: str) -> bool:
        """
        Delete a branch by adding to suggestions.
        
        Args:
            branch_name (str): Name of the branch to delete
        
        Returns:
            bool: True if the suggestion was added successfully, False otherwise
        """
        if branch_name not in self.branches:
            print(f"Branch '{branch_name}' does not exist.")
            return False
        
        # Prepare delete data
        delete_data = {"branch_name": branch_name}
        
        # Add to suggestions
        return self._add_operation_to_suggestions("delete", delete_data)
    
    def _update_previous_intents(self, target_branch: str, called_when: List[Dict[str, Any]]) -> None:
        """
        Update previous intents to point to the target branch.
        
        Args:
            target_branch (str): The branch that should be reached
            called_when (List[Dict]): List of previous intent configurations
        """
        for intent_config in called_when:
            previous_intent = intent_config.get("previous_intent")
            previous_response = intent_config.get("previous_response")
            response_of_previous_response = intent_config.get("response_of_previous_response")
            
            if not all([previous_intent, previous_response]):
                print(f"Invalid intent configuration: {intent_config}")
                continue
            
            # Find the branch with the previous intent
            for branch_name, branch_data in self.branches.items():
                if branch_data.get("intent") == previous_intent:
                    # Update the expected_user_responses to point to target_branch
                    if "expected_user_responses" in branch_data:
                        if previous_response in branch_data["expected_user_responses"]:
                            branch_data["expected_user_responses"][previous_response]["next"] = target_branch
                            if response_of_previous_response:
                                branch_data["expected_user_responses"][previous_response]["response"] = response_of_previous_response
                        else:
                            # Create new response entry
                            branch_data["expected_user_responses"][previous_response] = {
                                "next": target_branch,
                                "response": response_of_previous_response
                            }
                    break
    
    def _remove_branch_references(self, branch_name: str) -> None:
        """
        Remove all references to a branch from other branches.
        
        Args:
            branch_name (str): Name of the branch to remove references to
        """
        for branch_data in self.branches.values():
            if "expected_user_responses" in branch_data:
                for response_key, response_data in branch_data["expected_user_responses"].items():
                    if isinstance(response_data, dict) and response_data.get("next") == branch_name:
                        response_data["next"] = None
    
    def list_branch_names(self) -> List[str]:
        """
        Get a list of all branch names.
        
        Returns:
            List[str]: List of branch names
        """
        return list(self.branches.keys())
    
    def get_branch_by_intent(self, intent: str) -> Optional[str]:
        """
        Find branch name by intent.
        
        Args:
            intent (str): Intent to search for
        
        Returns:
            str or None: Branch name if found, None otherwise
        """
        for branch_name, branch_data in self.branches.items():
            if branch_data.get("intent") == intent:
                return branch_name
        return None
    
    def validate_branch_structure(self, branch_name: str) -> Dict[str, Any]:
        """
        Validate the structure of a branch and return validation results.
        
        Args:
            branch_name (str): Name of the branch to validate
        
        Returns:
            Dict: Validation results with 'valid' (bool) and 'errors' (list)
        """
        validation_result = {"valid": True, "errors": []}
        
        if branch_name not in self.branches:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Branch '{branch_name}' does not exist")
            return validation_result
        
        branch = self.branches[branch_name]
        
        # Check required fields
        required_fields = ["intent", "bot_prompt"]
        for field in required_fields:
            if field not in branch:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required field: {field}")
        
        # Check expected_user_responses structure if it exists
        if "expected_user_responses" in branch:
            responses = branch["expected_user_responses"]
            if not isinstance(responses, dict):
                validation_result["valid"] = False
                validation_result["errors"].append("expected_user_responses must be a dictionary")
            else:
                for response_key, response_data in responses.items():
                    if isinstance(response_data, dict):
                        # Check if 'next' field exists and points to a valid branch
                        if "next" in response_data and response_data["next"]:
                            next_branch = response_data["next"]
                            if next_branch not in self.branches:
                                validation_result["valid"] = False
                                validation_result["errors"].append(
                                    f"Response '{response_key}' points to non-existent branch '{next_branch}'"
                                )
        
        return validation_result
    
    def export_to_file(self, output_file: str) -> bool:
        """
        Export branches to a different JSON file.
        
        Args:
            output_file (str): Path to the output file
        
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(self.branches, file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting to file: {e}")
            return False

    def get_pending_suggestions(self) -> Dict[str, Any]:
        """
        Get all pending suggestions from the suggestions.json file.
        
        Returns:
            Dict: All pending suggestions
        """
        return self.suggestions.copy()

    def apply_suggestions(self, operation_indices: Optional[List[int]] = None, verbose: bool = True) -> Dict[str, Any]:
        """
        Apply suggestions from suggestions.json to branches.json with comprehensive reporting.
        
        Args:
            operation_indices (List[int], optional): Specific operation indices to apply. 
                                                   If None, applies all operations.
            verbose (bool): Whether to show detailed progress and results
        
        Returns:
            Dict: Results of the application with success/failure details
        """
        if verbose:
            self._print_separator("APPLYING SUGGESTIONS")
        
        if not self.suggestions.get("pending_operations"):
            result = {"success": True, "message": "No pending operations to apply", "applied": 0, "failed": 0}
            if verbose:
                print("📄 No pending operations to apply")
            return result
        
        # Show current state
        if verbose:
            self._show_current_state()
        
        # Preview changes
        if verbose:
            self._show_preview()
        
        operations = self.suggestions["pending_operations"]
        results = {"success": True, "applied": 0, "failed": 0, "errors": [], "operations_applied": []}
        
        # Determine which operations to apply
        if operation_indices is None:
            ops_to_apply = list(enumerate(operations))
        else:
            ops_to_apply = [(i, operations[i]) for i in operation_indices if 0 <= i < len(operations)]
        
        applied_indices = []
        
        if verbose:
            print(f"\n🔄 Processing {len(ops_to_apply)} operations...")
        
        for index, operation in ops_to_apply:
            try:
                operation_type = operation["operation_type"]
                data = operation["data"]
                branch_name = data.get("branch_name", "Unknown")
                
                if verbose:
                    print(f"\n📋 Operation {index}: {operation_type.upper()} '{branch_name}'")
                
                if operation_type == "create":
                    success = self._apply_create_operation(data)
                elif operation_type == "update":
                    success = self._apply_update_operation(data)
                elif operation_type == "delete":
                    success = self._apply_delete_operation(data)
                else:
                    success = False
                    error_msg = f"Unknown operation type: {operation_type}"
                    results["errors"].append(error_msg)
                    if verbose:
                        print(f"   ❌ {error_msg}")
                
                if success:
                    results["applied"] += 1
                    applied_indices.append(index)
                    results["operations_applied"].append({
                        "index": index,
                        "type": operation_type,
                        "branch_name": branch_name
                    })
                    if verbose:
                        print(f"   ✅ Successfully applied {operation_type} for '{branch_name}'")
                else:
                    results["failed"] += 1
                    results["success"] = False
                    if verbose:
                        print(f"   ❌ Failed to apply {operation_type} for '{branch_name}'")
                        
            except Exception as e:
                results["failed"] += 1
                results["success"] = False
                error_msg = f"Error applying operation {index}: {str(e)}"
                results["errors"].append(error_msg)
                if verbose:
                    print(f"   ❌ {error_msg}")
        
        # Remove applied operations from suggestions (in reverse order to maintain indices)
        for index in sorted(applied_indices, reverse=True):
            del self.suggestions["pending_operations"][index]
        
        # Save updated suggestions and branches
        self._save_suggestions()
        if results["applied"] > 0:
            self._save_branches()
        
        # Show detailed results
        if verbose:
            self._show_application_results(results)
            
            # Verify called_when applications if any were applied
            if results["applied"] > 0:
                self._verify_called_when_applications()
            
            # Show final state
            self._show_final_state()
        
        return results

    def _apply_create_operation(self, data: Dict[str, Any]) -> bool:
        """Apply a create operation to branches."""
        try:
            branch_name = data["branch_name"]
            branch_data = data["branch_data"]
            called_when = data.get("called_when")
            
            if branch_name in self.branches:
                print(f"Warning: Branch '{branch_name}' already exists, skipping creation")
                return False
            
            # Add the new branch
            self.branches[branch_name] = branch_data
            
            # Update previous intents if provided
            if called_when:
                print(f"Processing called_when configurations for '{branch_name}':")
                for intent_config in called_when:
                    previous_intent = intent_config.get("previous_intent")
                    previous_response = intent_config.get("previous_response")
                    response_of_previous_response = intent_config.get("response_of_previous_response")
                    
                    print(f"  Looking for intent '{previous_intent}' to add response '{previous_response}'")
                    
                    if not all([previous_intent, previous_response]):
                        print(f"    Invalid intent configuration: {intent_config}")
                        continue
                    
                    # Find the branch with the previous intent
                    found = False
                    for existing_branch_name, existing_branch_data in self.branches.items():
                        if existing_branch_data.get("intent") == previous_intent:
                            print(f"    Found branch '{existing_branch_name}' with intent '{previous_intent}'")
                            
                            # Ensure expected_user_responses exists
                            if "expected_user_responses" not in existing_branch_data:
                                existing_branch_data["expected_user_responses"] = {}
                            
                            # Add or update the response to point to our new branch
                            existing_branch_data["expected_user_responses"][previous_response] = {
                                "next": branch_name,
                                "response": response_of_previous_response
                            }
                            
                            print(f"    Added response '{previous_response}' pointing to '{branch_name}'")
                            found = True
                            break
                    
                    if not found:
                        print(f"    Warning: No branch found with intent '{previous_intent}'")
            
            return True
        except Exception as e:
            print(f"Error applying create operation: {e}")
            return False

    def _apply_update_operation(self, data: Dict[str, Any]) -> bool:
        """Apply an update operation to branches."""
        try:
            branch_name = data["branch_name"]
            
            if branch_name not in self.branches:
                print(f"Warning: Branch '{branch_name}' does not exist, skipping update")
                return False
            
            # Update fields if provided
            if "intent" in data:
                self.branches[branch_name]["intent"] = data["intent"]
            
            if "bot_prompt" in data:
                self.branches[branch_name]["bot_prompt"] = data["bot_prompt"]
            
            if "expected_user_responses" in data:
                self.branches[branch_name]["expected_user_responses"] = data["expected_user_responses"]
            
            if "action" in data:
                if data["action"] == "":  # Empty string to remove action
                    self.branches[branch_name].pop("action", None)
                else:
                    self.branches[branch_name]["action"] = data["action"]
            
            # Handle called_when if provided
            if "called_when" in data:
                self._update_previous_intents(branch_name, data["called_when"])
            
            return True
        except Exception as e:
            print(f"Error applying update operation: {e}")
            return False

    def _apply_delete_operation(self, data: Dict[str, Any]) -> bool:
        """Apply a delete operation to branches."""
        try:
            branch_name = data["branch_name"]
            
            if branch_name not in self.branches:
                print(f"Warning: Branch '{branch_name}' does not exist, skipping deletion")
                return False
            
            # Remove the branch
            del self.branches[branch_name]
            
            # Remove references to this branch from other branches
            self._remove_branch_references(branch_name)
            
            return True
        except Exception as e:
            print(f"Error applying delete operation: {e}")
            return False

    def clear_suggestions(self) -> bool:
        """
        Clear all pending suggestions without applying them.
        
        Returns:
            bool: True if suggestions were cleared successfully
        """
        self.suggestions = {"pending_operations": [], "timestamp": None}
        return self._save_suggestions()

    def preview_suggestions_effect(self) -> Dict[str, Any]:
        """
        Preview what would happen if all suggestions were applied without actually applying them.
        
        Returns:
            Dict: Preview of changes that would be made
        """
        if not self.suggestions.get("pending_operations"):
            return {"message": "No pending operations to preview"}
        
        preview = {
            "creates": [],
            "updates": [],
            "deletes": [],
            "potential_conflicts": []
        }
        
        temp_branches = self.branches.copy()
        
        for operation in self.suggestions["pending_operations"]:
            operation_type = operation["operation_type"]
            data = operation["data"]
            
            if operation_type == "create":
                branch_name = data["branch_name"]
                if branch_name in temp_branches:
                    preview["potential_conflicts"].append(f"Create: Branch '{branch_name}' already exists")
                else:
                    preview["creates"].append(branch_name)
                    temp_branches[branch_name] = data["branch_data"]
                    
            elif operation_type == "update":
                branch_name = data["branch_name"]
                if branch_name not in temp_branches:
                    preview["potential_conflicts"].append(f"Update: Branch '{branch_name}' does not exist")
                else:
                    preview["updates"].append(branch_name)
                    
            elif operation_type == "delete":
                branch_name = data["branch_name"]
                if branch_name not in temp_branches:
                    preview["potential_conflicts"].append(f"Delete: Branch '{branch_name}' does not exist")
                else:
                    preview["deletes"].append(branch_name)
                    del temp_branches[branch_name]
        
        return preview

    def _print_separator(self, title: str) -> None:
        """Print a nice separator with title"""
        print(f"\n{'='*60}")
        print(f"=== {title} ===")
        print('='*60)

    def _show_current_state(self) -> None:
        """Display current state of branches and suggestions"""
        branches = self.list_branch_names()
        print(f"📁 Current branches ({len(branches)}): {', '.join(branches[:5])}{'...' if len(branches) > 5 else ''}")
        
        suggestions = self.get_pending_suggestions()
        pending_ops = suggestions.get("pending_operations", [])
        print(f"📋 Pending operations: {len(pending_ops)}")
        
        if pending_ops:
            print("\n📝 Pending Operations:")
            for i, op in enumerate(pending_ops):
                op_type = op.get("operation_type", "UNKNOWN")
                branch_name = op.get("data", {}).get("branch_name", "Unknown")
                timestamp = op.get("timestamp", "Unknown")
                called_when = op.get("data", {}).get("called_when", [])
                
                print(f"  {i}: {op_type.upper()} '{branch_name}' at {timestamp[:19]}")
                if called_when:
                    for ai in called_when:
                        print(f"     🔗 {ai.get('previous_intent')} -> {ai.get('previous_response')} -> '{branch_name}'")

    def _show_preview(self) -> None:
        """Preview what the suggestions would do"""
        preview = self.preview_suggestions_effect()
        
        if "message" in preview:
            print(f"📄 {preview['message']}")
            return
        
        print("🔍 Preview of changes that would be applied:")
        
        if preview.get("creates"):
            print(f"  📝 CREATE: {', '.join(preview['creates'])}")
        
        if preview.get("updates"):
            print(f"  ✏️ UPDATE: {', '.join(preview['updates'])}")
        
        if preview.get("deletes"):
            print(f"  🗑️ DELETE: {', '.join(preview['deletes'])}")
        
        if preview.get("potential_conflicts"):
            print(f"  ⚠️ CONFLICTS:")
            for conflict in preview["potential_conflicts"]:
                print(f"     - {conflict}")

    def _show_application_results(self, results: Dict[str, Any]) -> None:
        """Show detailed application results"""
        print(f"\n📊 Application Results:")
        print(f"   ✅ Successfully applied: {results.get('applied', 0)}")
        print(f"   ❌ Failed to apply: {results.get('failed', 0)}")
        print(f"   🎯 Overall success: {results.get('success', False)}")
        
        if results.get("errors"):
            print(f"   🚨 Errors encountered:")
            for error in results["errors"]:
                print(f"      - {error}")
        
        if results.get("message"):
            print(f"   💬 Message: {results['message']}")
        
        # Show details of applied operations
        if results.get("operations_applied"):
            print(f"\n📋 Operations Applied:")
            for op in results["operations_applied"]:
                print(f"   ✅ {op['type'].upper()}: '{op['branch_name']}'")

    def _verify_called_when_applications(self) -> None:
        """Verify that called_when configurations were properly applied"""
        print(f"\n🔍 Verifying called_when applications...")
        
        # Check for branches that may have gotten new responses from called_when
        verification_count = 0
        branches_with_new_responses = []
        
        for branch_name, branch_data in self.branches.items():
            responses = branch_data.get("expected_user_responses", {})
            intent = branch_data.get("intent", "")
            
            # Look for recently added responses (this is a simplified check)
            # In a more sophisticated implementation, you could track which responses were added
            if responses:
                print(f"   📋 {branch_name} (intent: {intent}):")
                response_count = 0
                for response_key, response_data in responses.items():
                    if isinstance(response_data, dict):
                        next_branch = response_data.get("next", "None")
                        response_text = response_data.get("response", "No response text")
                        print(f"      ✅ '{response_key}' -> {next_branch}")
                        if response_text:
                            print(f"         💬 \"{response_text[:50]}{'...' if len(response_text) > 50 else ''}\"")
                        response_count += 1
                        
                if response_count > 0:
                    branches_with_new_responses.append(branch_name)
                    verification_count += 1
                    
                if verification_count >= 3:  # Limit output to avoid too much text
                    break
        
        if verification_count == 0:
            print("   📄 No branches with responses found to verify")

    def _show_final_state(self) -> None:
        """Show the final state after all operations"""
        self._print_separator("FINAL STATE")
        
        branches = self.list_branch_names()
        print(f"📁 Total branches: {len(branches)}")
        
        # Show newly created branches (those starting with common prefixes like "demo_", "payment_", etc.)
        new_branches = [b for b in branches if any(b.startswith(prefix) for prefix in ["demo_", "payment_", "new_"])]
        if new_branches:
            print(f"🆕 Recently created branches: {', '.join(new_branches)}")
            
            for branch_name in new_branches[:3]:  # Show details for first 3
                branch = self.read_branch(branch_name)
                if branch:
                    print(f"\n   📋 {branch_name}:")
                    print(f"      Intent: {branch.get('intent', 'N/A')}")
                    print(f"      Prompt: {branch.get('bot_prompt', 'N/A')[:60]}...")
                    responses = branch.get("expected_user_responses", {})
                    print(f"      Responses: {', '.join(responses.keys()) if responses else 'None'}")
                    if branch.get("action"):
                        print(f"      Action: {branch.get('action')}")
        
        # Check remaining suggestions
        suggestions = self.get_pending_suggestions()
        remaining_ops = len(suggestions.get("pending_operations", []))
        print(f"\n📋 Remaining pending operations: {remaining_ops}")
        
        print(f"\n🎉 Apply suggestions completed!")

    def read_interruptible_intents(self) -> Dict[str, Any]:
        """
        Read interruptible intents from branches.json
        
        Returns:
            Dict: Dictionary of interruptible intents
        """
        return self.branches.get("interruptible_intents", {})
    
    def is_interruptible_stage(self, stage_name: str, intent_name: str) -> bool:
        """
        Check if a stage can be interrupted by a specific intent
        
        Args:
            stage_name (str): Current conversation stage
            intent_name (str): Interruption intent name
            
        Returns:
            bool: True if stage can be interrupted by this intent
        """
        interruptible_intents = self.read_interruptible_intents()
        intent_data = interruptible_intents.get(intent_name, {})
        interruptible_stages = intent_data.get("interruptible_stages", [])
        
        return interruptible_stages == ["*"] or stage_name in interruptible_stages
    
    def get_interruption_response(self, intent_name: str) -> str:
        """
        Get the response template for an interruption intent
        
        Args:
            intent_name (str): Name of the interruption intent
            
        Returns:
            str: Response template for the interruption
        """
        interruptible_intents = self.read_interruptible_intents()
        intent_data = interruptible_intents.get(intent_name, {})
        return intent_data.get("response", "I understand. Let me help you with that.")
    
    def get_interruption_action(self, intent_name: str) -> str:
        """
        Get the action to take for an interruption intent
        
        Args:
            intent_name (str): Name of the interruption intent
            
        Returns:
            str: Action to take for the interruption
        """
        interruptible_intents = self.read_interruptible_intents()
        intent_data = interruptible_intents.get(intent_name, {})
        return intent_data.get("action", "acknowledge_and_redirect")
    
# Example usage and testing
if __name__ == "__main__":
    # Initialize the manager
    manager = BranchesManager("branches.json")
    
    # Example: Create a new branch
    expected_responses = {
        "yes": {
            "next": "payment_confirmation",
            "response": "Great! Let me process your payment."
        },
        "no": {
            "next": "alternative_options",
            "response": "I understand. Let me show you other options."
        }
    }
    
    called_when_config = [
        {
            "previous_intent": "confirm_policy",
            "previous_response": "interested",
            "response_of_previous_response": "I'm glad you're interested. Let's proceed with the payment."
        }
    ]
    
    # Create a new branch
    success = manager.create_branch(
        branch_name="payment_options",
        intent="show_payment_options",
        bot_prompt="Would you like to proceed with the online payment?",
        expected_user_responses=expected_responses,
        called_when=called_when_config
    )
    
    if success:
        print("Branch created successfully!")
    
    # Read a branch
    branch = manager.read_branch("greeting")
    if branch:
        print(f"Greeting branch: {branch}")
    
    # List all branch names
    branch_names = manager.list_branch_names()
    print(f"All branches: {branch_names}")
    
    # Validate a branch
    validation = manager.validate_branch_structure("greeting")
    print(f"Validation result: {validation}")
