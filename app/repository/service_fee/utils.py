from typing import List

def sort_fees_by_priority(rules: List) -> List:
    """
    Determines mathematical precedence explicitly. 
    A lower priority number means it should execute FIRST during calculation
    (e.g. Priority 1 Flat Fee applies before Priority 2 Percentage Tax).
    """
    return sorted(rules, key=lambda rule: rule.priority)
