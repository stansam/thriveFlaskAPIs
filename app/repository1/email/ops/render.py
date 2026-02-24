from flask import render_template, current_app
import os
from app.repository.email.exceptions import TemplateRenderingError

class RenderTemplate:
    def execute(self, template_name: str, context: dict) -> str:
        try:            
            if not template_name.startswith("email/"):
                template_path = f"email/{template_name}"
            else:
                template_path = template_name
                
            return render_template(template_path, **context)
        except Exception as e:
            raise TemplateRenderingError(f"Failed to render template {template_name}: {str(e)}") from e
