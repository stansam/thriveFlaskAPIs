import re

def validate_template_variables(template_text: str, payload: dict) -> bool:
    """
    Basic text template compiler checking variables (evaluating if template mappings natively 
    align to the payload dict strings passed prior to DB insertion).
    Matches variables like {{ variable_name }} or {variable_name}.
    """
    if not template_text:
        return True
        
    # Find all variables enclosed in {} or {{}}
    required_vars = re.findall(r'\{+([^}]+)\}+', template_text)
    required_vars = [v.strip() for v in required_vars]
    
    # Check if all required vars are in the payload
    for var in required_vars:
        if var not in payload:
            return False
            
    return True
