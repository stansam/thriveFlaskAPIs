from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import SubscriptionTier, SubscriptionStatus

class Company(BaseModel):
    __tablename__ = 'companies'

    name = db.Column(db.String(100), nullable=False)
    tax_id = db.Column(db.String(50))
    address = db.Column(db.String(255))
    contact_email = db.Column(db.String(120))
    
    employees = db.relationship('User', backref='company', lazy='dynamic')
    subscriptions = db.relationship('UserSubscription', backref='company', lazy='dynamic')

    def get_active_subscription(self):
        from app.models.payment import UserSubscription
        from app.models.enums import SubscriptionStatus
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return self.subscriptions.filter(
            UserSubscription.status == SubscriptionStatus.ACTIVE,
            UserSubscription.current_period_end > now
        ).first()

    def allowed_bookings(self):
        sub = self.get_active_subscription()
        if not sub:
            return 0
        from app.models.payment import SubscriptionPlan
        plan = SubscriptionPlan.query.get(sub.plan_id)
        return plan.booking_limit_count if plan else 0

    def __repr__(self):
        sub = self.get_active_subscription()
        tier_name = "None"
        if sub:
            from app.models.payment import SubscriptionPlan
            plan = SubscriptionPlan.query.get(sub.plan_id)
            if plan:
                tier_name = plan.tier.name
        return f"<Company {self.name} ({tier_name})>"
