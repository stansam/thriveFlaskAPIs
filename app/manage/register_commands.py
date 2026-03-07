from app.manage.commands.create_superuser import create_superuser
from app.manage.commands.create_plans import create_plans
from app.manage.commands.create_service_fees import create_service_fees
from app.manage.commands.create_testusers import create_testusers
from app.manage.commands.create_services import create_services
from app.manage.commands.create_packages import create_packages
from app.manage.commands.seed_database import seed_database

def register_cli_commands(app):
    app.cli.add_command(create_superuser)
    app.cli.add_command(create_plans)
    app.cli.add_command(create_service_fees)
    app.cli.add_command(create_testusers)
    app.cli.add_command(create_services)
    app.cli.add_command(create_packages)
    app.cli.add_command(seed_database)
