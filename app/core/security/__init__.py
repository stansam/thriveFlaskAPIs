# core/security.py
"""
Security utilities.

Responsibilities
----------------
1. Password hashing / verification   — Argon2id via argon2-cffi
2. JWT access & refresh tokens       — PyJWT HS256
3. Password reset tokens             — HMAC-signed, time-limited
4. TOTP / MFA                        — pyotp
5. Token denylist                    — Redis-backed (logout / rotation)
6. Flask decorators                  — @require_auth, @require_roles
7. Request context helpers           — get_current_user(), current_user_id()

Dependencies (add to requirements.txt)
---------------------------------------
    argon2-cffi>=23.1.0
    PyJWT>=2.8.0
    pyotp>=2.9.0
    redis>=5.0.0

All functions that touch the database or Redis are import-safe:
they import lazily inside function bodies to avoid circular imports
and app-context errors during module load.
"""
from app.core.security.password_reset import(
    create_reset_token, verify_reset_token
)

from app.core.security.password import(
    hash_password, verify_password, password_needs_rehash, generate_secure_random_password
)

from app.core.security.totp import(
    generate_totp_secret, get_totp_provisioning_uri, verify_totp, generate_totp_qr_data_url,
    is_totp_replayed, record_totp_use
)

from app.core.security.csrf import csrf_protect