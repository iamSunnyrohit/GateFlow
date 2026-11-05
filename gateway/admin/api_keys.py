from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from gateway.database import SessionLocal
from gateway.models import APIKeyModel
from gateway.security import generate_api_key, hash_api_key
from gateway.admin.dependencies import (
    require_admin,
    require_viewer_or_above,
)


router = APIRouter(
    prefix="/gateway/admin/api-keys",
    tags=["API Key Management"],
)

class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def serialize_key(api_key: APIKeyModel) -> dict:
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key_prefix": api_key.key_prefix,
        "is_active": api_key.is_active,
        "created_at": api_key.created_at,
        "last_used_at": api_key.last_used_at,
        "revoked_at": api_key.revoked_at,
    }


@router.post("", status_code=201)
def create_api_key(payload: APIKeyCreate, current_admin=Depends(require_admin),):

    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    with SessionLocal() as session:
        api_key = APIKeyModel(
            name=payload.name.strip(),
            key_hash=key_hash,
            key_prefix=raw_key[:16],
            is_active=True,
        )

        session.add(api_key)
        session.commit()
        session.refresh(api_key)

        result = serialize_key(api_key)

    return {
        "message": "API key created successfully. Store it securely; it will not be shown again.",
        "api_key": raw_key,
        "key_details": result,
    }


@router.get("")
def list_api_keys(current_admin=Depends(require_viewer_or_above),):

    with SessionLocal() as session:
        keys = (
            session.query(APIKeyModel)
            .order_by(APIKeyModel.id.desc())
            .all()
        )

        return {
            "total": len(keys),
            "api_keys": [serialize_key(key) for key in keys],
        }


@router.delete("/{key_id}")
def revoke_api_key(key_id: int, current_admin=Depends(require_admin),):

    with SessionLocal() as session:
        api_key = (
            session.query(APIKeyModel)
            .filter_by(id=key_id)
            .first()
        )

        if api_key is None:
            raise HTTPException(
                status_code=404,
                detail="API key not found",
            )

        if not api_key.is_active:
            raise HTTPException(
                status_code=409,
                detail="API key has already been revoked",
            )

        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)

        session.commit()

        result = serialize_key(api_key)

    return {
        "message": "API key revoked successfully",
        "key_details": result,
    }
