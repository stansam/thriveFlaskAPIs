import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.services import Service
from app.manage.data.services import services

@click.command("create-services")
@with_appcontext
def create_services():
    """Create services from sample data."""
    click.echo("Seeding services...")
    
    count = 0
    for service_data in services:
        existing_service = Service.query.filter_by(title=service_data['title']).first()
        
        if existing_service:
            click.echo(f"Service {service_data['title']} already exists.")
            continue
            
        new_service = Service(
            title=service_data['title'],
            description=service_data['description'],
            icon=service_data['icon']
        )
        db.session.add(new_service)
        count += 1
        
    db.session.commit()
    click.echo(f"Successfully seeded {count} services.")
