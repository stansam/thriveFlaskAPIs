from app.manage.register_commands import register_cli_commands
from flask import Blueprint

manage_bp = Blueprint("manage", __name__)

register_cli_commands(manage_bp)