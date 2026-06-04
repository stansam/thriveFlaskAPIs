import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_fee_snapshots

@click.command("seed-fee-snapshot")
@with_appcontext
def seed_fee_snapshot_command() -> None:
    """Seed ServiceFeeSnapshot table with sample data."""
    check_and_seed_fee_snapshots()
