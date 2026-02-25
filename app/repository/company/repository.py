from typing import Optional, List
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.company import Company
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.company.utils import sanitize_tax_id

class CompanyRepository(BaseRepository[Company]):
    """
    CompanyRepository encapsulating specific database queries and operations
    pertaining to corporate entities and employee groupings.
    """

    def __init__(self):
        super().__init__(Company)

    @handle_db_exceptions
    def get_all_companies(self, page: int = 1, limit: int = 50) -> dict:
        """Fetch a paginated list of all active or inactive corporate entities."""
        return self.get_paginated(page=page, per_page=limit)

    @handle_db_exceptions
    def find_by_tax_id(self, tax_id: str) -> Optional[Company]:
        """Lookup a corporate entity cleanly formatted by its taxation number."""
        clean_tax_id = sanitize_tax_id(tax_id)
        return self.model.query.filter_by(tax_id=clean_tax_id).first()

    @handle_db_exceptions
    def get_company_with_employees(self, company_id: str) -> Optional[Company]:
        """Fetch a company while eagerly loading its employee user relationships."""
        return self.model.query.options(
            joinedload(self.model.users)
        ).filter_by(id=company_id).first()

    @handle_db_exceptions
    def get_companies_by_status(self, is_active: bool) -> List[Company]:
        """Fetch all companies filtered by their soft-delete boolean status."""
        return self.model.query.filter_by(is_active=is_active).all()

    @handle_db_exceptions
    def update_company_details(self, company_id: str, data: dict) -> Optional[Company]:
        """Updates specific non-managed fields of a company record safely."""
        company = self.get_by_id(company_id)
        if not company:
            return None
            
        allowed_fields = {'name', 'address', 'contact_email', 'tax_id'}
        safe_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if 'tax_id' in safe_data:
            safe_data['tax_id'] = sanitize_tax_id(safe_data['tax_id'])
            
        return super().update(company, safe_data, commit=True)
