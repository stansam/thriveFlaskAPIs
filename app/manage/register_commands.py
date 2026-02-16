from app.manage.commands import runserver, create_superuser

def register_cli_commands(app):
    app.cli.add_command(runserver)
    app.cli.add_command(create_superuser)

