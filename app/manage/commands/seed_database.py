import click
from flask.cli import with_appcontext

from app.manage.commands.create_plans import create_plans
from app.manage.commands.create_service_fees import create_service_fees
from app.manage.commands.create_testusers import create_testusers
from app.manage.commands.create_services import create_services
from app.manage.commands.create_packages import create_packages

@click.command("seed-database")
@with_appcontext
@click.pass_context
def seed_database(ctx):
    """Run all sample data seeding commands sequentially."""
    click.echo("Starting comprehensive database seed...")
    
    try:
        ctx.invoke(create_plans)
        ctx.invoke(create_service_fees)
        ctx.invoke(create_services)
        ctx.invoke(create_packages)
        ctx.invoke(create_testusers)
        
        click.echo("Successfully completed database seed.")
    except Exception as e:
        click.echo(f"An error occurred during seeding: {str(e)}")