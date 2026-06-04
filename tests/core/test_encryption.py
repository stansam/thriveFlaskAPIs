"""
Unit tests for application-level symmetric encryption.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from app.core.security.encryption import encrypt_field, decrypt_field, _get_fernet


def test_encrypt_decrypt_round_trip():
    plaintext = "my-totp-secret-12345"
    ciphertext = encrypt_field(plaintext)
    assert ciphertext != plaintext
    assert ciphertext is not None

    decrypted = decrypt_field(ciphertext)
    assert decrypted == plaintext


def test_encrypt_none_returns_none():
    assert encrypt_field(None) is None
    assert decrypt_field(None) is None


def test_decrypt_tampered_raises():
    plaintext = "my-totp-secret-12345"
    ciphertext = encrypt_field(plaintext)
    assert ciphertext is not None
    
    # Tamper with the ciphertext (Fernet strings end with padding / are base64)
    tampered = ciphertext[:-5] + "XXXXX"
    with pytest.raises(ValueError, match="Failed to decrypt mfa_secret"):
        decrypt_field(tampered)


def test_no_key_returns_plaintext():
    # If settings.MFA_ENCRYPTION_KEY is empty, encrypt/decrypt should be no-ops
    from app.core.config import settings
    
    with patch.object(settings, "MFA_ENCRYPTION_KEY", ""):
        plaintext = "my-secret"
        ciphertext = encrypt_field(plaintext)
        assert ciphertext == plaintext
        
        decrypted = decrypt_field(ciphertext)
        assert decrypted == plaintext
