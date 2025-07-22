#!/usr/bin/env python3
"""
Script to validate branches.json file and identify broken links
Enhanced to ensure all conversation flows end in proper closure
"""

import json
import sys
from typing import Set, List, Tuple, Dict, Any

def analyze_branches():
    # Load the branches.json file
    with open('branches.json', 'r') as f:
        branches = json.load(f)
    
    # Get all branch names (exclude metadata)
    branch_names = set(branches.keys())
    metadata_branches = {"_metadata", "interruptible_intents"}
    actual_branches = branch_names - metadata_branches
    
    print(f"Total branches defined: {len(actual_branches)}")
    print(f"Branches: {sorted(actual_branches)}")
    print(f"Metadata sections: {sorted(metadata_branches)}")
    print("\n" + "="*50)
    
    # Find all "next" references
    next_references = set()
    broken_links = []
    
    def extract_next_refs(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key == "next" and isinstance(value, str):
                    next_references.add(value)
                    if value not in actual_branches and value not in metadata_branches:
                        broken_links.append((current_path, value))
                else:
                    extract_next_refs(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_next_refs(item, f"{path}[{i}]")
    
    extract_next_refs(branches)
    
    print(f"Total 'next' references found: {len(next_references)}")
    print(f"Next references: {sorted(next_references)}")
    
    # Check for broken links
    if broken_links:
        print(f"\n❌ BROKEN LINKS FOUND ({len(broken_links)}):")
        for path, broken_ref in broken_links:
            print(f"  - {path} -> '{broken_ref}' (branch does not exist)")
    else:
        print(f"\n✅ ALL LINKS ARE VALID!")
    
    # Enhanced: Identify conversation endpoints
    closure_branches = identify_closure_branches(branches, actual_branches)
    print(f"\n🏁 CONVERSATION ENDPOINTS IDENTIFIED ({len(closure_branches)}):")
    for branch_name, reason in closure_branches.items():
        print(f"  - {branch_name}: {reason}")
    
    # Check for unreachable branches
    reachable = set()
    to_visit = ["greeting"]  # Start with greeting as entry point
    
    while to_visit:
        branch_name = to_visit.pop()
        if branch_name in reachable or branch_name not in actual_branches:
            continue
        
        reachable.add(branch_name)
        branch = branches[branch_name]
        
        # Check direct "next" in branch
        if "next" in branch:
            to_visit.append(branch["next"])
        
        # Check "next" in expected_user_responses
        if "expected_user_responses" in branch:
            for response_key, response_data in branch["expected_user_responses"].items():
                if isinstance(response_data, dict) and "next" in response_data:
                    to_visit.append(response_data["next"])
    
    unreachable = actual_branches - reachable
    if unreachable:
        print(f"\n⚠️  UNREACHABLE BRANCHES ({len(unreachable)}):")
        for branch in sorted(unreachable):
            print(f"  - {branch}")
    else:
        print(f"\n✅ ALL BRANCHES ARE REACHABLE!")
    
    # Enhanced: Check if all branches can reach closure
    closure_reachability = check_closure_reachability(branches, actual_branches, closure_branches)
    branches_cant_reach_closure = []
    infinite_loops = []
    
    for branch_name in actual_branches:
        if branch_name in closure_branches:
            continue  # Skip branches that are already closures
            
        can_reach, path_info = closure_reachability[branch_name]
        if not can_reach:
            if path_info.get("infinite_loop"):
                infinite_loops.append((branch_name, path_info["loop_path"]))
            else:
                branches_cant_reach_closure.append((branch_name, path_info.get("dead_end", "Unknown reason")))
    
    if branches_cant_reach_closure:
        print(f"\n❌ BRANCHES CANNOT REACH CLOSURE ({len(branches_cant_reach_closure)}):")
        for branch_name, reason in branches_cant_reach_closure:
            print(f"  - {branch_name}: {reason}")
    else:
        print(f"\n✅ ALL BRANCHES CAN REACH CLOSURE!")
    
    if infinite_loops:
        print(f"\n⚠️  POTENTIAL INFINITE LOOPS DETECTED ({len(infinite_loops)}):")
        for branch_name, loop_path in infinite_loops:
            print(f"  - {branch_name}: {' -> '.join(loop_path)}")
    
    # Enhanced: Analyze closure diversity and suggest improvements
    closure_analysis = analyze_closure_diversity(branches, actual_branches, closure_branches)
    print(f"\n📊 CLOSURE ANALYSIS:")
    print(f"  - Total closure branches: {len(closure_branches)}")
    print(f"  - Closure types: {closure_analysis['types']}")
    print(f"  - Most common closure path: {closure_analysis['most_common_path']}")
    
    if closure_analysis['suggestions']:
        print(f"\n💡 CLOSURE IMPROVEMENT SUGGESTIONS:")
        for suggestion in closure_analysis['suggestions']:
            print(f"  - {suggestion}")
    
    # Enhanced: Check for orphaned conversation paths
    orphaned_paths = find_orphaned_paths(branches, actual_branches, reachable, closure_branches)
    if orphaned_paths:
        print(f"\n⚠️  ORPHANED CONVERSATION PATHS ({len(orphaned_paths)}):")
        for path_start, path_description in orphaned_paths:
            print(f"  - {path_start}: {path_description}")
    else:
        print(f"\n✅ NO ORPHANED CONVERSATION PATHS!")
    
    # Summary
    print(f"\n" + "="*50)
    print("ENHANCED VALIDATION SUMMARY:")
    print(f"  Total branches: {len(actual_branches)}")
    print(f"  Conversation endpoints: {len(closure_branches)}")
    print(f"  Broken links: {len(broken_links)}")
    print(f"  Unreachable branches: {len(unreachable)}")
    print(f"  Branches can't reach closure: {len(branches_cant_reach_closure)}")
    print(f"  Infinite loops: {len(infinite_loops)}")
    print(f"  Orphaned paths: {len(orphaned_paths)}")
    
    # Determine overall validation result
    critical_issues = broken_links or branches_cant_reach_closure or infinite_loops
    warning_issues = unreachable or orphaned_paths
    
    if critical_issues:
        print(f"\n❌ VALIDATION FAILED - Critical issues found!")
        return False
    elif warning_issues:
        print(f"\n⚠️  VALIDATION PASSED WITH WARNINGS - Non-critical issues found")
        return True
    else:
        print(f"\n✅ VALIDATION PASSED - All conversation flows properly end in closure!")
        return True


def identify_closure_branches(branches: Dict[str, Any], actual_branches: Set[str]) -> Dict[str, str]:
    """
    Identify branches that represent conversation endpoints/closures.
    
    Returns:
        Dict mapping branch names to reasons why they're considered closures
    """
    closure_branches = {}
    
    for branch_name in actual_branches:
        branch = branches[branch_name]
        
        # Check for explicit END_CALL action
        if branch.get("action") == "END_CALL":
            closure_branches[branch_name] = "Has END_CALL action"
            continue
        
        # Check for end_conversation intent
        if branch.get("intent") == "end_conversation":
            closure_branches[branch_name] = "Has end_conversation intent"
            continue
        
        # Check if branch has no outgoing paths (dead end)
        has_next = "next" in branch
        has_response_nexts = False
        
        if "expected_user_responses" in branch:
            for response_data in branch["expected_user_responses"].values():
                if isinstance(response_data, dict) and "next" in response_data:
                    has_response_nexts = True
                    break
        
        if not has_next and not has_response_nexts:
            closure_branches[branch_name] = "No outgoing paths (natural endpoint)"
    
    return closure_branches


def check_closure_reachability(branches: Dict[str, Any], actual_branches: Set[str], 
                             closure_branches: Dict[str, str]) -> Dict[str, Tuple[bool, Dict[str, Any]]]:
    """
    Check if each branch can eventually reach a closure branch.
    
    Returns:
        Dict mapping branch names to (can_reach_closure, path_info)
    """
    reachability = {}
    
    for branch_name in actual_branches:
        visited = set()
        path = []
        can_reach, path_info = can_reach_closure_dfs(
            branch_name, branches, closure_branches, visited, path
        )
        reachability[branch_name] = (can_reach, path_info)
    
    return reachability


def can_reach_closure_dfs(current_branch: str, branches: Dict[str, Any], 
                         closure_branches: Dict[str, str], visited: Set[str], 
                         path: List[str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Depth-first search to check if a branch can reach closure.
    
    Returns:
        (can_reach_closure, path_info_dict)
    """
    if current_branch in closure_branches:
        return True, {"path": path + [current_branch], "closure_type": closure_branches[current_branch]}
    
    if current_branch in visited:
        # Detected a loop
        loop_start_idx = path.index(current_branch) if current_branch in path else 0
        loop_path = path[loop_start_idx:] + [current_branch]
        return False, {"infinite_loop": True, "loop_path": loop_path}
    
    if current_branch not in branches:
        return False, {"dead_end": f"Branch '{current_branch}' does not exist"}
    
    visited.add(current_branch)
    path.append(current_branch)
    
    branch = branches[current_branch]
    next_branches = []
    
    # Collect all possible next branches
    if "next" in branch:
        next_branches.append(branch["next"])
    
    if "expected_user_responses" in branch:
        for response_data in branch["expected_user_responses"].values():
            if isinstance(response_data, dict) and "next" in response_data:
                next_branches.append(response_data["next"])
    
    if not next_branches:
        # This branch has no outgoing paths but isn't marked as closure
        path.pop()
        visited.remove(current_branch)
        return False, {"dead_end": f"Branch '{current_branch}' has no outgoing paths and is not a closure"}
    
    # Check if any next branch can reach closure
    for next_branch in next_branches:
        can_reach, _ = can_reach_closure_dfs(next_branch, branches, closure_branches, visited, path)
        if can_reach:
            path.pop()
            visited.remove(current_branch)
            return True, {"can_reach_via": next_branch}
    
    # No path to closure found
    path.pop()
    visited.remove(current_branch)
    return False, {"dead_end": f"No path to closure from '{current_branch}'"}


def find_orphaned_paths(branches: Dict[str, Any], actual_branches: Set[str], 
                       reachable: Set[str], closure_branches: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Find conversation paths that are isolated or problematic.
    
    Returns:
        List of (branch_name, description) tuples for orphaned paths
    """
    orphaned = []
    
    # Find branches that are reachable but lead nowhere useful
    for branch_name in reachable:
        if branch_name in closure_branches:
            continue
            
        branch = branches[branch_name]
        
        # Check if this branch only leads to unreachable branches
        next_branches = []
        
        if "next" in branch:
            next_branches.append(branch["next"])
        
        if "expected_user_responses" in branch:
            for response_data in branch["expected_user_responses"].values():
                if isinstance(response_data, dict) and "next" in response_data:
                    next_branches.append(response_data["next"])
        
        if next_branches:
            reachable_nexts = [nb for nb in next_branches if nb in reachable or nb in closure_branches]
            if not reachable_nexts:
                orphaned.append((branch_name, "All next branches are unreachable"))
    
    return orphaned


def analyze_closure_diversity(branches: Dict[str, Any], actual_branches: Set[str], 
                            closure_branches: Dict[str, str]) -> Dict[str, Any]:
    """
    Analyze the diversity and distribution of closure branches.
    
    Returns:
        Dict with analysis results and suggestions
    """
    analysis = {
        "types": {},
        "most_common_path": None,
        "suggestions": []
    }
    
    # Categorize closure types
    for branch_name, reason in closure_branches.items():
        closure_type = "unknown"
        if "END_CALL" in reason:
            closure_type = "explicit_end"
        elif "end_conversation" in reason:
            closure_type = "conversation_end"
        elif "natural endpoint" in reason:
            closure_type = "natural_end"
        
        analysis["types"][closure_type] = analysis["types"].get(closure_type, 0) + 1
    
    # Count paths leading to each closure
    closure_references = {}
    for branch_name in actual_branches:
        if branch_name in closure_branches:
            continue
            
        branch = branches[branch_name]
        next_branches = []
        
        if "next" in branch:
            next_branches.append(branch["next"])
        
        if "expected_user_responses" in branch:
            for response_data in branch["expected_user_responses"].values():
                if isinstance(response_data, dict) and "next" in response_data:
                    next_branches.append(response_data["next"])
        
        for next_branch in next_branches:
            if next_branch in closure_branches:
                closure_references[next_branch] = closure_references.get(next_branch, 0) + 1
    
    # Find most commonly referenced closure
    if closure_references:
        most_common = max(closure_references.items(), key=lambda x: x[1])
        analysis["most_common_path"] = f"{most_common[0]} ({most_common[1]} references)"
    
    # Generate suggestions
    if len(closure_branches) == 1:
        analysis["suggestions"].append("Consider adding different closure types for different outcomes (success, failure, callback, etc.)")
    
    if len(analysis["types"]) == 1:
        analysis["suggestions"].append("All closures are the same type - consider diversifying closure mechanisms")
    
    total_refs = sum(closure_references.values())
    if closure_references and len(closure_references) == 1:
        analysis["suggestions"].append(f"All {total_refs} paths lead to the same closure - consider adding outcome-specific closures")
    
    # Check for branches that should probably be closures but aren't
    potential_closures = []
    for branch_name in actual_branches:
        if branch_name in closure_branches:
            continue
        
        branch = branches[branch_name]
        
        # Check for goodbye/thank you patterns in bot_prompt
        prompt = branch.get("bot_prompt", "").lower()
        if any(word in prompt for word in ["thank you", "goodbye", "have a great day", "call ended"]):
            potential_closures.append(branch_name)
    
    if potential_closures:
        analysis["suggestions"].append(f"These branches might benefit from being marked as closures: {', '.join(potential_closures)}")
    
    return analysis


if __name__ == "__main__":
    success = analyze_branches()
    sys.exit(0 if success else 1)
