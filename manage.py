# from flask.cli import with_appcontext
# import click 

# @click.command()
# @with_appcontext
# def create_app_cli():
#     pass

from app import create_app

app = create_app()

def runserver():
    app.run(debug=True)

if __name__ == "__main__":
    runserver()