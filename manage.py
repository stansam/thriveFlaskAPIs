from flask.cli import with_appcontext
import click 

@click.command()
@with_appcontext
def create_app_cli():
    pass

