from flask.cli import with_appcontext
from app.models import User
from app.models.enums import UserRole
from app.manage.data.admin_user import admin1
import click 
from app.services.auth.service import AuthService
from app.dto.auth.schemas import RegisterRequestDTO
from app.extensions import db

@click.command("createsuperuser")
@with_appcontext
def create_superuser() -> str:
    users = User.query.filter_by(email=admin1["email"]).first()

    if users:
        click.echo("Admin user already exists")
        return
        
    try:
        auth_service = AuthService()
        admin_dto = RegisterRequestDTO(
            first_name=admin1.get("first_name", "Super"),
            last_name=admin1.get("last_name", "Admin"),
            email=admin1["email"],
            password=admin1["password"],
            phone=admin1.get("phone", "+1234567890"),
            role=UserRole.ADMIN
        )

        adminUser = auth_service.register_user(admin_dto)
        if adminUser:
            click.echo(f"Admin user created successfully. Email:{adminUser.email}")
    except Exception as e:
        click.echo(f"Admin user creation failed: {e}")
