from typing import Optional, List
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from app.extensions import db
from app.models.user import User
from app.models.enums import UserRole
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.user.utils import normalize_email

class UserRepository(BaseRepository[User]):
    """
    UserRepository encapsulating specific database queries and operations
    pertaining to the User identity and roles.
    """

    def __init__(self):
        super().__init__(User)

    @handle_db_exceptions
    def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Override to strictly omit soft-deleted identities dynamically."""
        return self.model.query.filter_by(is_active=True).limit(limit).offset(offset).all()

    @handle_db_exceptions
    def get_paginated(self, page: int = 1, per_page: int = 50) -> dict:
        """Override to strictly omit soft-deleted identities from paginated datasets dynamically."""
        pagination = self.model.query.filter_by(is_active=True).paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": pagination.items,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }

    @handle_db_exceptions
    def get_all_including_deleted(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Bypass the soft-delete filter natively if explicitly requested by an Admin."""
        return super().get_all(limit=limit, offset=offset)

    @handle_db_exceptions
    def find_by_email(self, email: str) -> Optional[User]:
        normalized = normalize_email(email)
        return self.model.query.filter(func.lower(self.model.email) == normalized).first()

    @handle_db_exceptions
    def find_by_company(self, company_id: str) -> List[User]:
        return self.model.query.filter_by(company_id=company_id, is_active=True).all()

    @handle_db_exceptions
    def find_by_verification_token(self, token: str) -> Optional[User]:
        return self.model.query.filter_by(email_verification_token=token).first()

    @handle_db_exceptions
    def save_user(self, user: User) -> User:
        """Saves a fully constructed User model directly, preserving instance states."""
        db.session.add(user)
        db.session.commit()
        return user

    @handle_db_exceptions
    def get_user_with_preferences(self, user_id: str) -> Optional[User]:
        return self.model.query.options(
            joinedload(self.model.preferences)
        ).filter_by(id=user_id).first()

    @handle_db_exceptions
    def update_user_preferences(self, user_id: str, prefs_dict: dict):
        from app.models.user_preference import UserPreference
        
        user = self.get_by_id(user_id)
        if not user.preferences:
            new_pref = UserPreference(user_id=user.id, **prefs_dict)
            db.session.add(new_pref)
            db.session.commit()
            return new_pref
        else:
            for key, val in prefs_dict.items():
                setattr(user.preferences, key, val)
            db.session.commit()
            return user.preferences

    @handle_db_exceptions
    def count_active_users_by_role(self, role: UserRole) -> int:
        return self.model.query.filter_by(
            role=role, 
            is_active=True
        ).count()

    @handle_db_exceptions
    def soft_delete_user(self, user_id: str) -> bool:
        """
        Marks a user as inactive. Requires soft-delete architecture
        via a `deleted_at` timestamp on BaseModel later.
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
            
        user.is_active = False
        db.session.commit()
        return True

    @handle_db_exceptions
    def restore_user(self, user_id: str) -> bool:
        """Restores a soft-deleted user."""
        user = self.get_by_id(user_id)
        if not user:
            return False
            
        user.is_active = True
        db.session.commit()
        return True
