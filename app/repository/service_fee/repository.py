from typing import List
from app.models.fee import ServiceFeeRule
from app.models.enums import FeeType
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.service_fee.utils import sort_fees_by_priority

class ServiceFeeRepository(BaseRepository[ServiceFeeRule]):
    """
    ServiceFeeRepository orchestrating lookup of active pricing modifiers
    applicable dynamically across varying checkout domains.
    """

    def __init__(self):
        super().__init__(ServiceFeeRule)

    @handle_db_exceptions
    def get_active_fee_rules_by_type(self, fee_type: FeeType) -> List[ServiceFeeRule]:
        """
        Fetches system-wide rules configured strictly for a specific domain mapping constraints.
        Results are reliably ordered by their `priority` index ensuring mathematical sequential evaluations
        (e.g., applying flat fees before percentage multipliers).
        """
        rules = self.model.query.filter_by(
            fee_type=fee_type,
            is_active=True
        ).all()
        
        # Enforce application calculation order cleanly Python-side 
        # protecting against arbitrary SQL sort implementations.
        return sort_fees_by_priority(rules)
