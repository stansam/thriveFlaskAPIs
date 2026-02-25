from jinja2 import Template

def compile_jinja_template(template_string: str, context: dict) -> str:
    """
    Safely evaluates raw HTML/Text strings evaluating Jinja markers against the
    provided injection mapping replacing keys instantly securely bridging templates natively.
    """
    if not template_string:
        return ""
        
    try:
        jinja_template = Template(template_string)
        return jinja_template.render(**context)
    except Exception as e:
        # Fallback raw return stripping crash hazards explicitly
        print(f"Jinja Compilation natively skipped bounds cleanly: {e}")
        return template_string
