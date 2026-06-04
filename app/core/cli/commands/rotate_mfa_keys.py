import click
from flask.cli import with_appcontext
from app.models.base import db as _db

@click.command("rotate-mfa-keys")
@click.option("--old-key", required=True, help="The previous Fernet encryption key used to decrypt current database values.")
@with_appcontext
def rotate_mfa_keys_command(old_key: str) -> None:
    """Rotate MFA encryption keys by decrypting secrets with the old key and re-encrypting with the new key."""
    from cryptography.fernet import Fernet
    from sqlalchemy import select
    from app.core.config import settings
    from app.models import User
    
    new_key = settings.MFA_ENCRYPTION_KEY
    if not new_key:
        click.echo("Error: MFA_ENCRYPTION_KEY is not set in application settings.")
        return
    if old_key == new_key:
        click.echo("Old key and new key are the same. No rotation needed.")
        return
        
    try:
        old_fernet = Fernet(old_key.encode())
        new_fernet = Fernet(new_key.encode())
    except Exception as exc:
        click.echo(f"Error parsing keys: {exc}")
        return
        
    users = _db.session.scalars(select(User).where(User._mfa_secret.isnot(None))).all()
    if not users:
        click.echo("No users found with enrolled MFA secrets.")
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
        click.echo("Some users failed to rotate (probably not encrypted with the specified old-key):")
        for uid, email, err in failed_users:
            click.echo(f"  - User {email} (id={uid}): {err}")
        click.echo("Aborting transaction. No database changes were saved.")
        return
        
    # Commit updates
    _db.session.commit()
    click.echo(f"Successfully rotated keys for {success_count} user(s).")
