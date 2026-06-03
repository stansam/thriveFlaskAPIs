"""
Unit tests for AuthService.

Covers: login, logout, change_password, request_password_reset,
reset_password, enroll_mfa, confirm_mfa_enrollment, disable_mfa.

All external dependencies (repos, UoW, denylist, Flask-Login, event bus)
are replaced with lightweight MagicMock / NullTokenDenylist instances.
The AuthService is tested in pure-Python isolation — no Flask app context
or database connection is required.
"""
from __future__ import annotations

import sys
import importlib.metadata
from datetime import datetime
from unittest.mock import MagicMock, patch, call

# ── Stub out C-extension / network deps before any app import ─────────────────
for _mod in ("bcrypt", "qrcode", "email_validator"):
    sys.modules.setdefault(_mod, MagicMock())

_real_version = importlib.metadata.version


def _mock_version(name: str) -> str:
    if name == "email-validator":
        return "2.0.0"
    return _real_version(name)


importlib.metadata.version = _mock_version  # type: ignore[assignment]
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from unittest.mock import MagicMock, patch

from app.core.token_denylist import NullTokenDenylist
from app.core.unit_of_work import IUnitOfWork
from app.core.errors.handlers import (
    InvalidCredentialsError,
    AccountInactiveError,
    MFARequiredError,
    MFAInvalidError,
    NotFoundError,
    BusinessRuleViolationError,
    PasswordResetTokenInvalidError,
)
from app.core.security import hash_password, generate_totp_secret
from app.dto import LoginRequest, PasswordChangeRequest, PasswordResetRequest
from app.enums import UserRole
from app.interface.auth import AuthService


# ── Fixtures ─────────────────────────────────────────────────────────────────

class _FakeUoW(IUnitOfWork):
    """In-memory Unit of Work for testing."""

    def __init__(self) -> None:
        self.committed = 0
        self.rolled_back = 0

    def __enter__(self) -> "_FakeUoW":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[override]
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self.committed += 1

    def rollback(self) -> None:
        self.rolled_back += 1


@pytest.fixture()
def uow() -> _FakeUoW:
    return _FakeUoW()


@pytest.fixture()
def denylist() -> NullTokenDenylist:
    return NullTokenDenylist()


@pytest.fixture()
def user_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def audit_service() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def service(user_repo, audit_service, uow, denylist) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        audit_service=audit_service,
        uow=uow,
        denylist=denylist,
    )


@pytest.fixture()
def mock_user() -> MagicMock:
    user = MagicMock()
    type(user).mfa_is_enrolled = property(
        lambda self: bool(self.mfa_secret and not str(self.mfa_secret).endswith(":pending"))
    )
    type(user).mfa_is_pending = property(
        lambda self: bool(self.mfa_secret and str(self.mfa_secret).endswith(":pending"))
    )
    user.id = "user-abc-123"
    user.email = "admin@thrive.com"
    user.password_hash = hash_password("ValidPassword1!")
    user.is_active = True
    user.mfa_secret = None
    user.last_login_at = None
    user.role = UserRole.AGENT
    user.to_audit_dict.return_value = {
        "id": "user-abc-123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by_id": None,
        "updated_by_id": None,
    }
    user.full_name = "Admin User"
    user.phone = "0712345678"
    return user


def _login_req(password: str = "ValidPassword1!", totp_code: str | None = None) -> LoginRequest:
    return LoginRequest.model_validate({
        "email": "admin@thrive.com",
        "password": password,
        "totp_code": totp_code,
    })


def _change_pw_req(
    current: str = "ValidPassword1!",
    new: str = "NewPassword2@",
    confirm: str = "NewPassword2@",
) -> PasswordChangeRequest:
    return PasswordChangeRequest.model_validate({
        "current_password": current,
        "new_password": new,
        "confirm_password": confirm,
    })


# ── Login ─────────────────────────────────────────────────────────────────────

@patch("app.interface.auth.services.event_bus")
@patch("app.interface.auth.services.login_user")
def test_login_success(mock_login_user, mock_bus, service, user_repo, audit_service, uow, mock_user):
    user_repo.find_by_email.return_value = mock_user

    result = service.login(_login_req(), ip_address="1.2.3.4")

    assert result.email == "admin@thrive.com"
    assert mock_user.last_login_at is not None
    user_repo.save.assert_called_once_with(mock_user)
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_login_user.assert_called_once()
    mock_bus.publish.assert_called_once()


@patch("app.interface.auth.services.login_user")
def test_login_unknown_email(mock_login, service, user_repo):
    """No user found — must still raise InvalidCredentialsError (not NameError)."""
    user_repo.find_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        service.login(_login_req())

    mock_login.assert_not_called()


@patch("app.interface.auth.services.login_user")
def test_login_wrong_password(mock_login, service, user_repo, mock_user):
    user_repo.find_by_email.return_value = mock_user

    with pytest.raises(InvalidCredentialsError):
        service.login(_login_req(password="WrongPass999!"))

    mock_login.assert_not_called()


@patch("app.interface.auth.services.login_user")
def test_login_inactive_account(mock_login, service, user_repo, mock_user):
    mock_user.is_active = False
    user_repo.find_by_email.return_value = mock_user

    with pytest.raises(AccountInactiveError):
        service.login(_login_req())

    mock_login.assert_not_called()


@patch("app.interface.auth.services.login_user")
def test_login_mfa_required_but_not_provided(mock_login, service, user_repo, mock_user):
    mock_user.mfa_secret = "SOMESECRET"  # active (no :pending suffix)
    user_repo.find_by_email.return_value = mock_user

    with pytest.raises(MFARequiredError):
        service.login(_login_req(totp_code=None))

    mock_login.assert_not_called()


@patch("app.interface.auth.services.login_user")
@patch("app.interface.auth.services.verify_totp", return_value=False)
def test_login_mfa_invalid_code(mock_verify, mock_login, service, user_repo, mock_user):
    mock_user.mfa_secret = "SOMESECRET"
    user_repo.find_by_email.return_value = mock_user

    with pytest.raises(MFAInvalidError):
        service.login(_login_req(totp_code="000000"))

    mock_login.assert_not_called()


@patch("app.interface.auth.services.event_bus")
@patch("app.interface.auth.services.login_user")
@patch("app.interface.auth.services.verify_totp", return_value=True)
def test_login_mfa_valid_code(mock_verify, mock_login, mock_bus, service, user_repo, mock_user):
    mock_user.mfa_secret = "SOMESECRET"
    user_repo.find_by_email.return_value = mock_user

    result = service.login(_login_req(totp_code="123456"))
    assert result.email == "admin@thrive.com"
    mock_login.assert_called_once()


# ── Logout ───────────────────────────────────────────────────────────────────

@patch("app.interface.auth.services.event_bus")
@patch("app.interface.auth.services.logout_user")
def test_logout_success(mock_logout, mock_bus, service, user_repo, audit_service, uow, mock_user):
    user_repo.get.return_value = mock_user

    service.logout("user-abc-123")

    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_logout.assert_called_once()
    mock_bus.publish.assert_called_once()


def test_logout_user_not_found(service, user_repo):
    user_repo.get.return_value = None

    with pytest.raises(NotFoundError):
        service.logout("nonexistent-id")


# ── Change password ───────────────────────────────────────────────────────────

@patch("app.interface.auth.services.event_bus")
def test_change_password_success(mock_bus, service, user_repo, audit_service, uow, mock_user):
    user_repo.get.return_value = mock_user

    service.change_password("user-abc-123", _change_pw_req(), actor_id="user-abc-123")

    user_repo.save.assert_called_once()
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()


def test_change_password_wrong_current(service, user_repo, mock_user):
    user_repo.get.return_value = mock_user

    with pytest.raises(InvalidCredentialsError):
        service.change_password(
            "user-abc-123",
            _change_pw_req(current="BadCurrent1!"),
            actor_id="user-abc-123",
        )


def test_change_password_same_as_current(service, user_repo, mock_user):
    user_repo.get.return_value = mock_user

    with pytest.raises(BusinessRuleViolationError):
        service.change_password(
            "user-abc-123",
            _change_pw_req(new="ValidPassword1!", confirm="ValidPassword1!"),
            actor_id="user-abc-123",
        )


# ── Request password reset ────────────────────────────────────────────────────

@patch("app.interface.auth.services.event_bus")
@patch("app.interface.auth.services.create_reset_token", return_value="mock-reset-token")
def test_request_reset_known_email(mock_token, mock_bus, service, user_repo, uow, mock_user):
    user_repo.find_by_email.return_value = mock_user

    result = service.request_password_reset("admin@thrive.com")

    assert result.message  # always returns generic message
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()


def test_request_reset_unknown_email(service, user_repo, uow):
    """Unknown email must return identical response — no enumeration."""
    user_repo.find_by_email.return_value = None

    result = service.request_password_reset("ghost@thrive.com")

    assert result.message  # same response shape
    assert uow.committed == 0  # no DB write for unknown email


# ── Reset password ────────────────────────────────────────────────────────────

@patch("app.interface.auth.services.event_bus")
@patch("app.interface.auth.services.verify_reset_token", return_value="user-abc-123")
def test_reset_password_success(mock_verify, mock_bus, service, user_repo, audit_service, uow, mock_user):
    user_repo.get.return_value = mock_user
    data = PasswordResetRequest.model_validate({
        "token": "valid.token.sig",
        "new_password": "BrandNew3#",
        "confirm_password": "BrandNew3#",
    })

    service.reset_password(data)

    user_repo.save.assert_called_once()
    audit_service.log.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()


@patch("app.interface.auth.services.verify_reset_token", side_effect=Exception("bad"))
def test_reset_password_invalid_token(mock_verify, service):
    data = PasswordResetRequest.model_validate({
        "token": "bad.token",
        "new_password": "BrandNew3#",
        "confirm_password": "BrandNew3#",
    })

    with pytest.raises(PasswordResetTokenInvalidError):
        service.reset_password(data)


@patch("app.interface.auth.services.verify_reset_token", return_value="user-abc-123")
def test_reset_password_replayed_token(mock_verify, service, user_repo, mock_user):
    """Replayed token (already consumed in denylist) must be rejected."""
    user_repo.get.return_value = mock_user
    # Mark as already consumed
    service._reset_pw_op._denylist.consume("replayed.token.sig", ttl_seconds=1800)

    data = PasswordResetRequest.model_validate({
        "token": "replayed.token.sig",
        "new_password": "BrandNew3#",
        "confirm_password": "BrandNew3#",
    })

    # NullTokenDenylist always returns False for is_consumed — use a real-ish denylist
    # Swap to a simple in-memory denylist for this test
    from app.core.token_denylist import ITokenDenylist

    class _SingleUseDenylist(ITokenDenylist):
        def __init__(self):
            self._used: set[str] = set()

        def consume(self, token: str, ttl_seconds: int) -> bool:
            if token in self._used:
                return False
            self._used.add(token)
            return True

        def is_consumed(self, token: str) -> bool:
            return token in self._used

    service._reset_pw_op._denylist = _SingleUseDenylist()
    service._reset_pw_op._denylist.consume("replayed.token.sig", ttl_seconds=1800)  # pre-consume

    with pytest.raises(PasswordResetTokenInvalidError):
        service.reset_password(data)


# ── MFA Enroll ───────────────────────────────────────────────────────────────

@patch("app.interface.auth.services.generate_totp_qr_data_url", return_value="data:image/png;base64,ABC")
@patch("app.interface.auth.services.get_totp_provisioning_uri", return_value="otpauth://totp/test")
@patch("app.interface.auth.services.generate_totp_secret", return_value="FAKEBASE32SECRET")
def test_enroll_mfa_success(mock_secret, mock_uri, mock_qr, service, user_repo, uow, mock_user):
    user_repo.get.return_value = mock_user

    result = service.enroll_mfa("user-abc-123", actor_id="user-abc-123")

    assert result.provisioning_uri == "otpauth://totp/test"
    assert result.qr_code_data_url.startswith("data:")
    assert mock_user.mfa_secret == "FAKEBASE32SECRET:pending"
    assert uow.committed == 1


def test_enroll_mfa_already_enrolled(service, user_repo, mock_user):
    mock_user.mfa_secret = "ACTIVE_SECRET"  # no :pending suffix
    user_repo.get.return_value = mock_user

    with pytest.raises(BusinessRuleViolationError):
        service.enroll_mfa("user-abc-123", actor_id="user-abc-123")


# ── MFA Confirm ───────────────────────────────────────────────────────────────

@patch("app.interface.auth.services.event_bus")
@patch("app.interface.auth.services.verify_totp", return_value=True)
def test_confirm_mfa_success(mock_verify, mock_bus, service, user_repo, audit_service, uow, mock_user):
    mock_user.mfa_secret = "REALSECRET:pending"
    user_repo.get.return_value = mock_user

    service.confirm_mfa_enrollment(
        "user-abc-123", totp_code="123456", actor_id="user-abc-123"
    )

    assert mock_user.mfa_secret == "REALSECRET"
    user_repo.save.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()


@patch("app.interface.auth.services.verify_totp", return_value=False)
def test_confirm_mfa_wrong_code(mock_verify, service, user_repo, mock_user):
    mock_user.mfa_secret = "REALSECRET:pending"
    user_repo.get.return_value = mock_user

    with pytest.raises(MFAInvalidError):
        service.confirm_mfa_enrollment("user-abc-123", "wrong", "user-abc-123")


def test_confirm_mfa_not_started(service, user_repo, mock_user):
    mock_user.mfa_secret = None
    user_repo.get.return_value = mock_user

    with pytest.raises(MFAInvalidError):
        service.confirm_mfa_enrollment("user-abc-123", "123456", "user-abc-123")


# ── MFA Disable ───────────────────────────────────────────────────────────────

@patch("app.interface.auth.services.event_bus")
@patch("app.interface.auth.services.verify_totp", return_value=True)
def test_disable_mfa_success(mock_verify, mock_bus, service, user_repo, audit_service, uow, mock_user):
    mock_user.mfa_secret = "ACTIVE_SECRET"
    user_repo.get.return_value = mock_user

    service.disable_mfa("user-abc-123", totp_code="123456", actor_id="user-abc-123")

    assert mock_user.mfa_secret is None
    user_repo.save.assert_called_once()
    assert uow.committed == 1
    mock_bus.publish.assert_called_once()


@patch("app.interface.auth.services.verify_totp", return_value=False)
def test_disable_mfa_wrong_code(mock_verify, service, user_repo, mock_user):
    mock_user.mfa_secret = "ACTIVE_SECRET"
    user_repo.get.return_value = mock_user

    with pytest.raises(MFAInvalidError):
        service.disable_mfa("user-abc-123", "bad-code", "user-abc-123")


def test_disable_mfa_not_enrolled(service, user_repo, mock_user):
    mock_user.mfa_secret = None
    user_repo.get.return_value = mock_user

    with pytest.raises(MFAInvalidError):
        service.disable_mfa("user-abc-123", "123456", "user-abc-123")
