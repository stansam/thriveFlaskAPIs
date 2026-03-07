import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.package import Package, PackageItinerary, PackageInclusion, PackageMedia
from app.manage.data.packages import packages

@click.command("create-packages")
@with_appcontext
def create_packages():
    """Create travel packages from sample data."""
    click.echo("Seeding travel packages...")
    
    count = 0
    for pkg_data in packages:
        existing_pkg = Package.query.filter_by(slug=pkg_data['slug']).first()
        
        if existing_pkg:
            click.echo(f"Package {pkg_data['title']} already exists.")
            continue
            
        new_pkg = Package(
            title=pkg_data['title'],
            slug=pkg_data['slug'],
            description=pkg_data.get('description'),
            duration_nights=pkg_data['duration_nights'],
            duration_days=pkg_data['duration_days'],
            country=pkg_data.get('country'),
            city=pkg_data.get('city'),
            currency=pkg_data.get('currency', 'USD'),
            is_active=pkg_data.get('is_active', True),
            is_featured=pkg_data.get('is_featured', False),
            meta_title=pkg_data.get('meta_title'),
            meta_description=pkg_data.get('meta_description')
        )
        
        db.session.add(new_pkg)
        db.session.flush() # get id
        
        # Add media
        for media_data in pkg_data.get('media', []):
            new_media = PackageMedia(
                package_id=new_pkg.id,
                image_url=media_data['image_url'],
                is_featured=media_data.get('is_featured', False),
                display_order=media_data.get('display_order', 0)
            )
            db.session.add(new_media)
            
        # Add itineraries
        for it_data in pkg_data.get('itineraries', []):
            new_itinerary = PackageItinerary(
                package_id=new_pkg.id,
                day_number=it_data['day_number'],
                title=it_data.get('title'),
                description=it_data.get('description'),
                location=it_data.get('location')
            )
            db.session.add(new_itinerary)
            
        # Add inclusions
        for inc_data in pkg_data.get('inclusions', []):
            new_inclusion = PackageInclusion(
                package_id=new_pkg.id,
                description=inc_data['description'],
                is_included=inc_data.get('is_included', True)
            )
            db.session.add(new_inclusion)
            
        count += 1
        click.echo(f"Created package: {pkg_data['title']}")
        
    db.session.commit()
    click.echo(f"Successfully seeded {count} packages.")
