from flask.cli import with_appcontext
from app.models import User
from app.manage.data.admin_user import admin1
import click 

@click.command("create_superuser")
@with_appcontext
def create_superuser() -> tuple[str, str]:
    users = User.query.filter_by(email=admin1[email]).first()

    if users:
        return "Admin user already exists"

    adminUser, error = CreateUser(admin1, user_role="ADMIN")
    if error:
        return None, error
    return f"Admin user created successfully. Email:{adminUser.email}", None
