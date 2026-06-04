import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_notifications

@click.command("seed-notification-delivery")
@with_appcontext
def seed_notification_delivery_command() -> None:
    """Seed NotificationDelivery table with sample data."""
    check_and_seed_notifications()
