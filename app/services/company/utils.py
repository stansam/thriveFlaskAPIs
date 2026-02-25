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
    
    # Enforce strictly scaling bounds mapped physically against the active Subscription Plan logic:
    seat_limit = plan.fee_waiver_rules.get("max_employees") if plan.fee_waiver_rules else None
    
    # If the tier specifically omits a `max_employees` limit, it is considered unbounded (e.g. Enterprise Custom tier).
    if seat_limit is not None and current_employees_count >= seat_limit:
        raise ValueError(f"Seat limit exceeded. The current active plan tier strictly allows only {seat_limit} registered employees.")
