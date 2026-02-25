from app.models.company import Company
from app.models.payment import SubscriptionPlan

def enforce_employee_limits(company: Company) -> None:
    """
    Evaluates active seat counts dynamically against an overarching SaaS Subscription tier
    before allowing a 'manage_employees (ADD)' operation to process.
    """
    sub = company.get_active_subscription()
    if not sub:
        # Prevent completely entirely if the underlying enterprise account has lapsed billing
        raise ValueError("Cannot add employees: No active subscription present for this Company.")
        
    plan = SubscriptionPlan.query.get(sub.plan_id)
    if not plan:
         raise ValueError("Invalid internal subscription plan mapping detected.")
         
    # Optional logic: plan might have a 'seat_limit' tracked in JSON `fee_waiver_rules` or natively.
    # We query the total actively joined employees strictly mapped to the Company natively:
    current_employees_count = company.employees.count()
    
    # In a fully fleshed app, `seat_limit` would be a native column on SubscriptionPlan. 
    # For now, we enforce a hardcap mock interceptor ensuring the scaling bounds trigger:
    seat_limit = plan.fee_waiver_rules.get("max_employees", 50) if plan.fee_waiver_rules else 50
    
    if current_employees_count >= seat_limit:
        raise ValueError(f"Seat limit exceeded. The current active plan tier only allows {seat_limit} registered employees.")
