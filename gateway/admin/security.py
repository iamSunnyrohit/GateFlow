import os

from datetime import datetime, timedelta, timezone

import jwt

from pwdlib import PasswordHash


# Password hashing using Argon2
password_hasher = PasswordHash.recommended()


# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

JWT_ALGORITHM = "HS256"

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)


def get_jwt_secret():
    """
    Return the JWT secret.

    Never use a hardcoded development secret.
    """

    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY is missing. Configure it in your .env file."
        )

    return JWT_SECRET_KEY


def hash_password(password: str) -> str:
    """
    Hash an admin password using Argon2.
    """

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a password against its stored Argon2 hash.
    """

    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    admin_id: int,
    role: str,
) -> str:
    """
    Generate a signed JWT access token.
    """

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(admin_id),
        "role": role,
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    token = jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )

    return token