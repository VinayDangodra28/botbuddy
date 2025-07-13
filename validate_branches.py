#!/usr/bin/env python3
"""
Script to validate branches.json file and identify broken links
"""

import json
import sys

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
    
    print(f"\nTotal 'next' references found: {len(next_references)}")
    print(f"Next references: {sorted(next_references)}")
    
    # Check for broken links
    if broken_links:
        print(f"\n❌ BROKEN LINKS FOUND ({len(broken_links)}):")
        for path, broken_ref in broken_links:
            print(f"  - {path} -> '{broken_ref}' (branch does not exist)")
    else:
        print(f"\n✅ ALL LINKS ARE VALID!")
    
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
    
    # Summary
    print(f"\n" + "="*50)
    print("SUMMARY:")
    print(f"  Total branches: {len(actual_branches)}")
    print(f"  Broken links: {len(broken_links)}")
    print(f"  Unreachable branches: {len(unreachable)}")
    
    if broken_links or unreachable:
        print(f"\n❌ VALIDATION FAILED")
        return False
    else:
        print(f"\n✅ VALIDATION PASSED")
        return True

if __name__ == "__main__":
    success = analyze_branches()
    sys.exit(0 if success else 1)
