from typing import Optional
from app.models.user import User
from app.models.profile import UserPreference
from app.repository import repositories
from app.dto.user.schemas import UpdateProfileDTO, UpdatePreferencesDTO
from app.services.user.utils import scramble_pii_string

class UserService:
    """
    UserService orchestrates domain logic explicitly for the User bounded context,
    managing settings configurations and executing irreversible account terminations safely.
    """

    def __init__(self):
        self.user_repo = repositories.user

    def get_profile(self, user_id: str) -> Optional[dict]:
        """
        Retrieves the unified user view recursively assembling preferences
        and active overarching enterprise subscriptions natively under `.to_dict()`.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
            
        profile_data = user.to_dict()
        if user.preferences:
            profile_data['preferences'] = {
                'email_notifications': user.preferences.email_notifications,
                'sms_notifications': user.preferences.sms_notifications,
                'marketing_opt_in': user.preferences.marketing_opt_in,
                'currency': user.preferences.currency,
                'timezone': user.preferences.timezone
            }
        else:
            profile_data['preferences'] = {}
            
        return profile_data

    def update_profile(self, user_id: str, data: UpdateProfileDTO) -> Optional[User]:
        """
        Validates structurally explicitly permitted field mappings mutating demographics
        leveraging strict dataclass parameter stripping beforehand.
        """
        # Strip out Nones retaining strictly what the frontend explicitly passed for update
        update_dict = {k: v for k, v in data.__dict__.items() if v is not None}
        if not update_dict:
            return self.user_repo.get_by_id(user_id)
            
        return self.user_repo.update(user_id, update_dict, commit=True)

    def update_preferences(self, user_id: str, prefs: UpdatePreferencesDTO) -> Optional[UserPreference]:
        """Upserts settings constraints determining global alerts/currencies cleanly."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
            
        prefs_dict = {k: v for k, v in prefs.__dict__.items() if v is not None}
        
        if not user.preferences:
            # Create fresh preferences block if entirely absent initially
            new_pref = UserPreference(user_id=user.id, **prefs_dict)
            from app.extensions import db
            db.session.add(new_pref)
            db.session.commit()
            return new_pref
        else:
            # Safely loop update explicit matches without clobbering existing unaffected keys natively
            for key, val in prefs_dict.items():
                setattr(user.preferences, key, val)
            from app.extensions import db
            db.session.commit()
            return user.preferences

    def delete_account(self, user_id: str) -> bool:
        """
        Orchestrates irreversible data protection wiping logic. Leverages the soft delete 
        repository mechanic while physically overwriting PII permanently masking traces.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
            
        # GDPR Compliant Scrambling of explicit identification markers while retaining DB integrity (e.g. for financial reporting maps)
        wipe_data = {
            "first_name": "Deleted",
            "last_name": "User",
            "phone": scramble_pii_string(user.phone) if user.phone else None,
            "email": scramble_pii_string(user.email, is_email=True),
            "avatar_url": None,
            "password_hash": "[DELETED_ACCOUNT]" # Purge the active cryptographic verification completely limiting future breach payload leverage
        }
        
        self.user_repo.update(user_id, wipe_data, commit=False)
        return self.user_repo.soft_delete_user(user_id)
