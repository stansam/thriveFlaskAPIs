import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_audits

@click.command("seed-audit")
@with_appcontext
def seed_audit_command() -> None:
    """Seed AuditLog table with sample data."""
    check_and_seed_audits()
