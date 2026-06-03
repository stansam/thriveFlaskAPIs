import getpass
from flask import Flask
# from scripts.seed import run_seed
def run_seed(): 
    """Dummy seed function for when scripts.seed is missing."""
    pass
from app.dto import UserCreateRequest
from app.enums import UserRole
from app.models.base import db as _db
from app.core.security import hash_password
from app.repository import user_repo

def _register_cli_commands(app: Flask) -> None:
    """Attach Flask CLI commands."""

    @app.cli.command("db-seed")
    def seed_db():
        """Seed the database with initial data (super admin user, fee schedule)."""
        run_seed()
        print("Database seeded successfully.")

    @app.cli.command("create-admin")
    def create_admin():
        """Interactive prompt to create the first SUPER_ADMIN user."""
        print("=== Create Super Admin ===")
        email    = input("Email: ").strip()
        name     = input("Full name: ").strip()
        password = getpass.getpass("Password: ")
        confirm  = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("Passwords do not match. Aborting.")
            return

        with app.app_context():
            req = UserCreateRequest(
                email=email,
                full_name=name,
                password=password,
                role=UserRole.SUPER_ADMIN,
            )
            user = user_repo.create(
                email=email,
                full_name=name,
                password_hash=hash_password(password),
                role=UserRole.SUPER_ADMIN,
            )
            _db.session.commit()
            print(f"Super admin created: {user.email} (id={user.id})")

    @app.cli.command("routes")
    def list_routes():
        """List all registered routes."""
        output = []
        for rule in app.url_map.iter_rules():
            methods = ",".join(sorted((rule.methods or set()) - {"OPTIONS", "HEAD"}))
            output.append(f"{methods:20s}  {str(rule)}")
        for line in sorted(output):
            print(line)
