from flask.cli import with_appcontext
import click 
import os
from app.extensions import socketio

@click.command("runserver")
@click.option("--host", default=os.getenv("HOST", "0.0.0.0"))
@click.option("--port", default=os.getenv("PORT", 5000))
@with_appcontext
def runserver(host, port):
    debug = os.getenv("DEBUG", True)
    socketio.run(app, host=host, port=port, debug=debug)