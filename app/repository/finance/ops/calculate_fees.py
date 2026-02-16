from app.models import ServiceFeeRule
from app.models.enums import FeeType
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.finance.exceptions import DatabaseError

class CalculateFees:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, fee_type_name: str, amount: float) -> list[dict]:
        try:
            # fee_type_name should match one of the FeeType enum values (e.g. "flight_domestic")
            try:
                fee_type = FeeType(fee_type_name)
            except ValueError:
                 # If invalid fee type, return empty or raise? Returning empty is safer for now.
                 return []

            rules = self.db.query(ServiceFeeRule).filter_by(fee_type=fee_type, is_active=True).all()
            
            fees = []
            for rule in rules:
                fee_amount = 0.0
                if rule.amount_percent > 0:
                    fee_amount += amount * (rule.amount_percent / 100.0)
                
                if rule.amount_fixed > 0:
                    fee_amount += rule.amount_fixed
                
                fees.append({
                    "rule_id": rule.id,
                    "description": rule.name,
                    "amount": round(fee_amount, 2),
                    "currency": rule.currency
                })
            
            return fees
            
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while calculating fees: {str(e)}") from e
