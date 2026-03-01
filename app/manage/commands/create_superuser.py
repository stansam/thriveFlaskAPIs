from flask.cli import with_appcontext
from app.models import User
from app.models.enums import UserRole
import click 
from app.services.auth.service import AuthService
from app.dto.auth.schemas import RegisterRequestDTO
from app.extensions import db

@click.command("createsuperuser")
@click.option("--first-name", prompt=True)
@click.option("--last-name", prompt=True)
@click.option("--email", prompt=True)
@click.option("--phone", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_superuser(first_name, last_name, email, phone, password) -> str:
    users = User.query.filter_by(email=email).first()

    if users:
        click.echo("Admin user already exists")
        return
        
    try:
        auth_service = AuthService()
        admin_dto = RegisterRequestDTO(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            phone=phone,
            role=UserRole.ADMIN
        )

        adminUser = auth_service.register_user(admin_dto)
        if adminUser:
            click.echo(f"Admin user created successfully. Email:{adminUser.email}")
    except Exception as e:
        click.echo(f"Admin user creation failed: {e}")
