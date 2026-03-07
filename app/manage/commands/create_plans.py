import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.payment import SubscriptionPlan
from app.models.enums import SubscriptionTier
from app.manage.data.plans import plans

@click.command("create-plans")
@with_appcontext
def create_plans():
    """Create subscription plans from sample data."""
    click.echo("Seeding subscription plans...")
    
    count = 0
    for plan_data in plans:
        # Check if plan already exists
        tier_enum = SubscriptionTier[plan_data['tier']]
        existing_plan = SubscriptionPlan.query.filter_by(tier=tier_enum).first()
        
        if existing_plan:
            click.echo(f"Plan {plan_data['name']} already exists.")
            continue
            
        new_plan = SubscriptionPlan(
            name=plan_data['name'],
            tier=tier_enum,
            price_monthly=plan_data['price_monthly'],
            currency=plan_data['currency'],
            booking_limit_count=plan_data['booking_limit_count'],
            fee_waiver_rules=plan_data['fee_waiver_rules']
        )
        db.session.add(new_plan)
        count += 1
        
    db.session.commit()
    click.echo(f"Successfully seeded {count} subscription plans.")
