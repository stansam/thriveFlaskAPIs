import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.service_fee import ServiceFeeRule
from app.models.enums import FeeType
from app.manage.data.fees import fees

@click.command("create-service-fees")
@with_appcontext
def create_service_fees():
    """Create service fee rules from sample data."""
    click.echo("Seeding service fee rules...")
    
    count = 0
    for fee_data in fees:
        fee_type_enum = FeeType[fee_data['fee_type']]
        existing_fee = ServiceFeeRule.query.filter_by(fee_type=fee_type_enum, name=fee_data['name']).first()
        
        if existing_fee:
            click.echo(f"Fee Rule {fee_data['name']} already exists.")
            continue
            
        new_fee = ServiceFeeRule(
            name=fee_data['name'],
            fee_type=fee_type_enum,
            amount_fixed=fee_data['amount_fixed'],
            amount_percent=fee_data['amount_percent'],
            priority=fee_data['priority']
        )
        db.session.add(new_fee)
        count += 1
        
    db.session.commit()
    click.echo(f"Successfully seeded {count} service fee rules.")
