import click
import getpass
from flask.cli import with_appcontext
from app.enums import UserRole
from app.models.base import db as _db
from app.core.security import hash_password
from app.repository import user_repo

@click.command("create-admin")
@with_appcontext
def create_admin_command() -> None:
    """Interactive prompt to create the first SUPER_ADMIN user."""
    click.echo("=== Create Super Admin ===")
    email = input("Email: ").strip()
    name = input("Full name: ").strip()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        click.echo("Passwords do not match. Aborting.")
        return

    user = user_repo.create(
        email=email,
        full_name=name,
        password_hash=hash_password(password),
        role=UserRole.SUPER_ADMIN,
    )
    _db.session.commit()
    click.echo(f"Super admin created: {user.email} (id={user.id})")
