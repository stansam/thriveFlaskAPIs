import click
from flask import current_app
from flask.cli import with_appcontext

@click.command("routes")
@with_appcontext
def routes_command() -> None:
    """List all registered routes."""
    output = []
    for rule in current_app.url_map.iter_rules():
        methods = ",".join(sorted((rule.methods or set()) - {"OPTIONS", "HEAD"}))
        output.append(f"{methods:20s}  {str(rule)}")
    for line in sorted(output):
        click.echo(line)
