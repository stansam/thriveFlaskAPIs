import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.company import Company
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.enums import UserRole, Gender
from app.manage.data.testusers import companies, users
from app.services.auth.service import AuthService
from app.dto.auth.schemas import RegisterRequestDTO

@click.command("create-testusers")
@with_appcontext
def create_testusers():
    """Create test companies and users."""
    click.echo("Seeding test companies...")
    
    company_objects = []
    
    for comp_data in companies:
        existing_comp = Company.query.filter_by(contact_email=comp_data['contact_email']).first()
        if existing_comp:
            click.echo(f"Company {comp_data['name']} already exists.")
            company_objects.append(existing_comp)
            continue
            
        new_comp = Company(
            name=comp_data['name'],
            tax_id=comp_data['tax_id'],
            address=comp_data['address'],
            contact_email=comp_data['contact_email']
        )
        db.session.add(new_comp)
        company_objects.append(new_comp)
        click.echo(f"Created company: {comp_data['name']}")
        
    db.session.commit()
    
    click.echo("Seeding test users...")
    auth_service = AuthService()
    user_count = 0
    
    for user_data in users:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if existing_user:
            click.echo(f"User {user_data['email']} already exists.")
            continue
            
        try:
            role_enum = UserRole[user_data['role']]
            
            # Using auth service to handle password hashing and other base logic, 
            # though manual creation can also work. Opting for manual to easily set preferences.
            new_user = User(
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                phone=user_data['phone'],
                role=role_enum,
                gender=Gender[user_data['gender']] if 'gender' in user_data else None,
                email_verified=True
            )
            new_user.set_password(user_data['password'])
            
            # Assign company if index is provided
            if 'company_index' in user_data and user_data['company_index'] < len(company_objects):
                new_user.company_id = company_objects[user_data['company_index']].id
                
            db.session.add(new_user)
            db.session.flush() # flush to get user id for preferences
            
            # Add preferences
            pref_data = user_data.get('preferences', {})
            new_prefs = UserPreference(
                user_id=new_user.id,
                currency=pref_data.get('currency', 'USD'),
                language=pref_data.get('language', 'en'),
                timezone=pref_data.get('timezone', 'UTC'),
                marketing_opt_in=pref_data.get('marketing_opt_in', False),
                email_updates=pref_data.get('email_updates', True)
            )
            db.session.add(new_prefs)
            user_count += 1
            click.echo(f"Created test user: {user_data['email']}")
            
        except Exception as e:
            click.echo(f"Failed to create user {user_data['email']}: {str(e)}")
            
    db.session.commit()
    click.echo(f"Successfully seeded {user_count} test users.")
