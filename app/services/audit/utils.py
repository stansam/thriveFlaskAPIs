from typing import Dict, Any

def construct_change_diff(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts delta deviations natively avoiding massive JSON bloat by targeting
    explicit mutations traversing dictionary payloads neatly.
    
    Returns standard explicit diffs -> {"status": {"old": "PENDING", "new": "COMPLETED"}}
    """
    if not old_state:
        return {"action_type": "CREATE", "new_values": new_state}
    if not new_state:
        return {"action_type": "DELETE", "old_values": old_state}
        
    changes = {}
    
    # Check intersecting modifications explicitly natively
    for key, new_val in new_state.items():
        if key in old_state:
             old_val = old_state[key]
             if str(old_val) != str(new_val):
                  changes[key] = {"old": old_val, "new": new_val}
        else:
             changes[key] = {"old": None, "new": new_val}
             
    return changes
