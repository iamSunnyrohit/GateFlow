import hashlib
import secrets


def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key.
    The raw key is shown to the client only once.
    """
    return f"gf_live_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """
    Convert an API key into a SHA-256 hash.
    """
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()
