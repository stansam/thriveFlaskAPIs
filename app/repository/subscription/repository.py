from typing import Optional, List
from datetime import datetime, timezone
from app.extensions import db
from app.models.payment import UserSubscription, SubscriptionPlan
from app.models.enums import SubscriptionStatus
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.subscription.utils import get_expiry_cutoff_date

class SubscriptionRepository(BaseRepository[UserSubscription]):
    """
    SubscriptionRepository encapsulating specific database queries and operations
    pertaining to billing plans, active user/company subscriptions, and usage logic.
    """

    def __init__(self):
        super().__init__(UserSubscription)

    @handle_db_exceptions
    def get_active_subscription_for_user(self, user_id: str) -> Optional[UserSubscription]:
        """Fetch active subscription explicitly linked to an individual user."""
        now = datetime.now(timezone.utc)
        return self.model.query.filter(
            self.model.user_id == user_id,
            self.model.status == SubscriptionStatus.ACTIVE,
            self.model.current_period_end > now
        ).first()

    @handle_db_exceptions
    def get_active_subscription_for_company(self, company_id: str) -> Optional[UserSubscription]:
        """Fetch active subscription explicitly linked to a corporate company entity."""
        now = datetime.now(timezone.utc)
        return self.model.query.filter(
            self.model.company_id == company_id,
            self.model.status == SubscriptionStatus.ACTIVE,
            self.model.current_period_end > now
        ).first()

    @handle_db_exceptions
    def get_subscription_plan_by_name(self, name: str) -> Optional[SubscriptionPlan]:
        """Lookup a generic subscription plan configuration by its tier string name."""
        return SubscriptionPlan.query.filter_by(name=name, is_active=True).first()

    @handle_db_exceptions
    def list_expiring_subscriptions(self, days_until_expiry: int) -> List[UserSubscription]:
        """Query for subscriptions set to expire within a specific lookahead boundary duration."""
        cutoff_date = get_expiry_cutoff_date(days_until_expiry)
        now = datetime.now(timezone.utc)
        
        return self.model.query.filter(
            self.model.status == SubscriptionStatus.ACTIVE,
            self.model.current_period_end > now,
            self.model.current_period_end <= cutoff_date
        ).all()

    @handle_db_exceptions
    def update_usage_count(self, subscription_id: str, increment_by: int) -> Optional[UserSubscription]:
        """Atomically increments the dynamic current billing cycle usage counter."""
        subscription = self.get_by_id(subscription_id)
        if not subscription:
            return None
            
        subscription.bookings_used_this_period += increment_by
        db.session.commit()
        return subscription
