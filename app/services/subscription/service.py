from typing import Optional
from datetime import datetime, timezone
from app.models.payment import UserSubscription, SubscriptionPlan
from app.models.enums import SubscriptionStatus, EntityType
from app.repository import repositories
from app.dto.subscription.schemas import SubscribeToPlanDTO, UpgradePlanDTO
from app.services.subscription.utils import calculate_period_end_date

class SubscriptionService:
    """
    SubscriptionService maneuvers SaaS tier entitlements explicitly tying external billing 
    gateway logic softly onto underlying User/Company booking capabilities.
    """

    def __init__(self):
        self.sub_repo = repositories.subscription
        self.user_repo = repositories.user
        self.company_repo = repositories.company
        self.invoice_repo = repositories.invoice

    def subscribe_to_plan(self, payload: SubscribeToPlanDTO) -> UserSubscription:
        """
        Activates a fresh entitlement cycle bridging the requested Plan cleanly onto
        the User or Enterprise Company target explicitly initiating invoicing logic natively.
        """
        # 1. Fetch Plan 
        plan = SubscriptionPlan.query.get(payload.plan_id)
        if not plan or not plan.is_active:
            raise ValueError("Invalid or inactive subscription plan requested.")

        # 2. Check targets
        user_id = payload.entity_id if payload.entity_type == EntityType.USER else None
        company_id = payload.entity_id if payload.entity_type == EntityType.COMPANY else None
        
        if user_id and not self.user_repo.get_by_id(user_id):
            raise ValueError("User target entity does not exist.")
        if company_id and not self.company_repo.get_by_id(company_id):
            raise ValueError("Company target entity does not exist.")

        # 3. Formulate the explicit temporal tracking interval (e.g., exactly 30 days upfront)
        now = datetime.now(timezone.utc)
        period_end = calculate_period_end_date(now)

        # 4. Create explicitly
        sub_data = {
            "user_id": user_id,
            "company_id": company_id,
            "plan_id": plan.id,
            "status": SubscriptionStatus.ACTIVE,
            "current_period_start": now,
            "current_period_end": period_end,
            "auto_renew": True
        }
        
        new_subscription = self.sub_repo.create(sub_data, commit=True)
        
        # 5. Generate upfront Invoice cleanly binding back to the created `new_subscription` 
        # TODO: Route this through `PaymentService` or generate explicitly Native via Repo:
        invoice_desc = f"Initial Subscription Charge - {plan.name}"
        # For simplicity, defer invoice emission details exactly to a later Payment module phase.
        
        return new_subscription

    def upgrade_plan(self, payload: UpgradePlanDTO) -> UserSubscription:
        """
        Safely swaps the ongoing active bounding parameters over to the newly requested plan
        adjusting temporal windows implicitly if necessary.
        """
        subscription = self.sub_repo.get_by_id(payload.subscription_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
             raise ValueError("Only actively established tracking subscriptions qualify for an upgrade.")
             
        new_plan = SubscriptionPlan.query.get(payload.new_plan_id)
        if not new_plan or not new_plan.is_active:
            raise ValueError("Target upgrade plan is inaccessible.")
            
        # Calculate exact prorated differentials
        now = datetime.now(timezone.utc)
        period_start = subscription.current_period_start.replace(tzinfo=timezone.utc) if subscription.current_period_start.tzinfo is None else subscription.current_period_start
        period_end = subscription.current_period_end.replace(tzinfo=timezone.utc) if subscription.current_period_end.tzinfo is None else subscription.current_period_end
        
        total_days = (period_end - period_start).days or 1
        unused_days = max(0, (period_end - now).days)
        
        old_plan = SubscriptionPlan.query.get(subscription.plan_id)
        
        if old_plan and unused_days > 0:
            old_prorated_credit = (old_plan.price_monthly / total_days) * unused_days
            new_prorated_cost = (new_plan.price_monthly / total_days) * unused_days
            differential = max(0, new_prorated_cost - old_prorated_credit)
            
            if differential > 0:
                # Issue differential invoice natively
                from app.models.payment import Invoice
                import uuid
                from app.models.enums import InvoiceStatus
                
                differential_invoice = Invoice(
                    user_id=subscription.user_id,
                    subscription_id=subscription.id,
                    invoice_number=f"INV-UPG-{uuid.uuid4().hex[:8].upper()}",
                    issued_date=now.date(),
                    due_date=now.date(), 
                    total_amount=round(differential, 2),
                    currency=new_plan.currency,
                    status=InvoiceStatus.ISSUED
                )
                self.invoice_repo.create({"user_id": subscription.user_id, "subscription_id": subscription.id, "invoice_number": f"INV-UPG-{uuid.uuid4().hex[:8].upper()}", "issued_date": now.date(), "due_date": now.date(), "total_amount": round(differential, 2), "currency": new_plan.currency, "status": InvoiceStatus.ISSUED}, commit=False)
            
        update_dict = {"plan_id": new_plan.id}
        # Reset the allowed booking count constraints explicitly given a new bounding environment
        update_dict["bookings_used_this_period"] = 0 
        
        updated_sub = self.sub_repo.update(subscription.id, update_dict, commit=True)
        return updated_sub

    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Instructs the chronological engine to deliberately allow the ongoing entitlement
        period to lapse seamlessly avoiding abrupt immediate severed access (unless requested specifically).
        """
        subscription = self.sub_repo.get_by_id(subscription_id)
        if not subscription:
            return False
            
        # Do not flip to EXPIRED yet. The Cron worker handles EXPIRED flipping native upon `current_period_end` passing cleanly
        self.sub_repo.update(subscription_id, {"auto_renew": False}, commit=True)
        return True

    def check_booking_eligibility(self, user_id: str) -> bool:
        """
        Interrogates exactly whether an upfront checkout payload legally possesses the
        structural bounds allowing traversal matching against `User.can_book()`.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
            
        return user.can_book()
