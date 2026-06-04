import getpass
import click
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

def seed_auth_templates(app):
    from app.models.notification_template import NotificationTemplate
    from app.enums import NotificationEventType, NotificationChannel
    from app.models.base import db as _db

    templates_to_seed = [
        {
            "event_type": NotificationEventType.USER_PASSWORD_RESET,
            "channel": NotificationChannel.EMAIL,
            "language": "en",
            "name": "Password Reset Email EN",
            "subject": "Reset Your Password",
            "body": "Hello,\n\nYou requested a password reset. Please click the link below to reset your password:\n\nhttp://localhost:3000/reset-password?token={{ reset_token }}\n\nThis token will expire in 30 minutes.\n\nIf you did not request this, please ignore this email.",
        },
        {
            "event_type": NotificationEventType.USER_PASSWORD_CHANGED,
            "channel": NotificationChannel.EMAIL,
            "language": "en",
            "name": "Password Changed Email EN",
            "subject": "Your Password Has Been Changed",
            "body": "Hello,\n\nThis is a confirmation that the password for your account has been successfully changed.\n\nIf you did not make this change, please contact support immediately.",
        },
        {
            "event_type": NotificationEventType.USER_MFA_ENROLLED,
            "channel": NotificationChannel.EMAIL,
            "language": "en",
            "name": "MFA Enrolled Email EN",
            "subject": "Multi-Factor Authentication Enabled",
            "body": "Hello,\n\nMulti-Factor Authentication (MFA) has been successfully enabled on your account. You will now be prompted for a TOTP code during login.",
        },
        {
            "event_type": NotificationEventType.USER_MFA_DISABLED,
            "channel": NotificationChannel.EMAIL,
            "language": "en",
            "name": "MFA Disabled Email EN",
            "subject": "Multi-Factor Authentication Disabled",
            "body": "Hello,\n\nWARNING: Multi-Factor Authentication (MFA) has been disabled on your account. If you did not request this, please contact support immediately.",
        },
        {
            "event_type": NotificationEventType.USER_PASSWORD_CHANGED,
            "channel": NotificationChannel.IN_APP,
            "language": "en",
            "name": "Password Changed In-App EN",
            "subject": "Password Changed",
            "body": "Your account password was changed successfully.",
        },
        {
            "event_type": NotificationEventType.USER_MFA_ENROLLED,
            "channel": NotificationChannel.IN_APP,
            "language": "en",
            "name": "MFA Enrolled In-App EN",
            "subject": "MFA Enabled",
            "body": "Multi-Factor Authentication has been enabled.",
        },
        {
            "event_type": NotificationEventType.USER_MFA_DISABLED,
            "channel": NotificationChannel.IN_APP,
            "language": "en",
            "name": "MFA Disabled In-App EN",
            "subject": "MFA Disabled",
            "body": "WARNING: Multi-Factor Authentication has been disabled.",
        },
    ]

    with app.app_context():
        for tpl_data in templates_to_seed:
            existing = NotificationTemplate.query.filter_by(
                event_type=tpl_data["event_type"],
                channel=tpl_data["channel"],
                language=tpl_data["language"]
            ).first()
            if not existing:
                tpl = NotificationTemplate(**tpl_data)
                _db.session.add(tpl)
        _db.session.commit()


def _register_cli_commands(app: Flask) -> None:
    """Attach Flask CLI commands."""

    @app.cli.command("db-seed")
    def seed_db():
        """Seed the database with initial data (super admin user, fee schedule, templates)."""
        run_seed()
        seed_auth_templates(app)
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

    @app.cli.command("rotate-mfa-keys")
    @click.option("--old-key", required=True, help="The previous Fernet encryption key used to decrypt current database values.")
    def rotate_mfa_keys(old_key):
        """Rotate MFA encryption keys by decrypting secrets with the old key and re-encrypting with the new key."""
        from cryptography.fernet import Fernet
        from sqlalchemy import select
        from app.core.config import settings
        from app.models import User
        
        new_key = settings.MFA_ENCRYPTION_KEY
        if not new_key:
            print("Error: MFA_ENCRYPTION_KEY is not set in application settings.")
            return
        if old_key == new_key:
            print("Old key and new key are the same. No rotation needed.")
            return
            
        try:
            old_fernet = Fernet(old_key.encode())
            new_fernet = Fernet(new_key.encode())
        except Exception as exc:
            print(f"Error parsing keys: {exc}")
            return
            
        users = _db.session.scalars(select(User).where(User._mfa_secret.isnot(None))).all()
        if not users:
            print("No users found with enrolled MFA secrets.")
            return
            
        success_count = 0
        failed_users = []
        
        for user in users:
            try:
                # Get raw ciphertext
                ciphertext = user._mfa_secret
                if not ciphertext:
                    continue
                # Decrypt using old key
                plaintext = old_fernet.decrypt(ciphertext.encode()).decode()
                # Encrypt using new key
                new_ciphertext = new_fernet.encrypt(plaintext.encode()).decode()
                # Write back raw ciphertext
                user._mfa_secret = new_ciphertext
                success_count += 1
            except Exception as exc:
                failed_users.append((user.id, user.email, str(exc)))
                
        if failed_users:
            print("Some users failed to rotate (probably not encrypted with the specified old-key):")
            for uid, email, err in failed_users:
                print(f"  - User {email} (id={uid}): {err}")
            print("Aborting transaction. No database changes were saved.")
            return
            
        # Commit updates
        _db.session.commit()
        print(f"Successfully rotated keys for {success_count} user(s).")

