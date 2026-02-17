from flask.cli import with_appcontext
from app.models import User
from app.manage.data.admin_user import admin1
import click 
from app.repository.user import UserService
from app.extensions import db

@click.command("createsuperuser")
@with_appcontext
def create_superuser() -> str:
    users = User.query.filter_by(email=admin1["email"]).first()

    if users:
        click.echo("Admin user already exists")
    try:
        user_service = UserService(db.session)

        adminUser = user_service.CreateUser(admin1)
        if adminUser:
            click.echo(f"Admin user created successfully. Email:{adminUser.email}")
    except Exception as e:
        click.echo(f"Admin user creation failed: {e}")
