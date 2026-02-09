"""
Security utilities for Prodway.

Provides:
- Field-level encryption for sensitive data
- PII hashing for audit logs
- Token management
"""

import os
import base64
import hashlib
import secrets
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_encryption_key() -> bytes:
    """
    Get or derive encryption key from environment.

    For production, set ENCRYPTION_KEY as a base64-encoded 32-byte key.
    If not set, derives from ENCRYPTION_SECRET using PBKDF2.
    """
    key = os.environ.get("ENCRYPTION_KEY")
    if key:
        return base64.urlsafe_b64decode(key)

    # Derive from secret
    secret = os.environ.get("ENCRYPTION_SECRET", "dev-secret-change-in-prod")
    salt = os.environ.get("ENCRYPTION_SALT", "prodway-salt").encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )

    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


def encrypt_field(value: str) -> str:
    """
    Encrypt a string field for storage.

    Returns base64-encoded encrypted value.
    """
    if not value:
        return ""

    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_field(encrypted_value: str) -> str:
    """
    Decrypt a previously encrypted field.
    """
    if not encrypted_value:
        return ""

    key = get_encryption_key()
    f = Fernet(key)
    encrypted = base64.urlsafe_b64decode(encrypted_value.encode())
    return f.decrypt(encrypted).decode()


def hash_pii(value: str) -> str:
    """
    One-way hash for PII in logs.

    Use this for logging emails, names, etc. so they're
    searchable but not readable.
    """
    if not value:
        return ""

    salt = os.environ.get("PII_HASH_SALT", "prodway-pii").encode()
    return hashlib.sha256(salt + value.encode()).hexdigest()[:16]


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """Generate an API key in the format 'pw_live_xxx'."""
    token = secrets.token_urlsafe(24)
    return f"pw_live_{token}"


def mask_email(email: str) -> str:
    """
    Mask an email for display.

    john.doe@company.com -> j***e@company.com
    """
    if not email or "@" not in email:
        return email

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]

    return f"{masked_local}@{domain}"


def mask_token(token: str, visible_chars: int = 4) -> str:
    """
    Mask a token for display.

    sk-ant-xxx...xxx -> sk-ant-xxx...•••
    """
    if not token or len(token) <= visible_chars * 2:
        return "•" * 12

    return token[:visible_chars] + "•••" + token[-visible_chars:]


# Credential validators
def is_valid_slack_token(token: str) -> bool:
    """Check if token looks like a valid Slack token."""
    return token.startswith(("xoxb-", "xoxp-", "xapp-"))


def is_valid_stripe_key(key: str) -> bool:
    """Check if key looks like a valid Stripe key."""
    return key.startswith(("sk_test_", "sk_live_", "rk_test_", "rk_live_"))


def is_valid_anthropic_key(key: str) -> bool:
    """Check if key looks like a valid Anthropic key."""
    return key.startswith("sk-ant-")
