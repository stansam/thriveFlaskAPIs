from flask_login import UserMixin
from app.models.user import User

class FlaskLoginUser(UserMixin):
    """Thin adapter wrapping the domain User entity for Flask-Login."""

    def __init__(self, user: User) -> None:
        self._user = user

    def get_id(self) -> str:
        return self._user.id

    # @property
    # def is_active(self) -> bool:
    #     return self._user.is_active

    # @property
    # def is_authenticated(self) -> bool:
    #     return True

    # @property
    # def is_anonymous(self) -> bool:
    #     return False

    @property
    def domain_user(self) -> User:
        """Access underlying domain entity."""
        return self._user
