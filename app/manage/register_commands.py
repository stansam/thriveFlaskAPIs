from app.manage.commands import create_superuser

def register_cli_commands(app):
    app.cli.add_command(create_superuser)

