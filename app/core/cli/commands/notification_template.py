import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_notification_templates

@click.command("seed-notification-template")
@with_appcontext
def seed_notification_template_command() -> None:
    """Seed NotificationTemplate table with sample data."""
    check_and_seed_notification_templates()
