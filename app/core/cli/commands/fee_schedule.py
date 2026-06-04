import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_fee_schedules

@click.command("seed-fee-schedule")
@with_appcontext
def seed_fee_schedule_command() -> None:
    """Seed ServiceFeeSchedule table with sample data."""
    check_and_seed_fee_schedules()
