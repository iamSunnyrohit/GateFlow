from datetime import datetime, timezone

from fastapi import HTTPException, Request

from gateway.database import SessionLocal
from gateway.models import APIKeyModel
from gateway.security import hash_api_key


async def require_api_key(request: Request):
    """
    Validate the API key supplied in the X-API-Key header.

    OPTIONS requests are allowed through for browser CORS preflight.
    """

    if request.method == "OPTIONS":
        return

    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide the X-API-Key header.",
        )

    key_hash = hash_api_key(api_key)

    with SessionLocal() as session:
        stored_key = (
            session.query(APIKeyModel)
            .filter(
                APIKeyModel.key_hash == key_hash,
                APIKeyModel.is_active.is_(True),
            )
            .first()
        )

        if stored_key is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or revoked API key.",
            )

        stored_key.last_used_at = datetime.now(timezone.utc)
        session.commit()

        request.state.api_key_id = stored_key.id
        request.state.api_key_name = stored_key.name
