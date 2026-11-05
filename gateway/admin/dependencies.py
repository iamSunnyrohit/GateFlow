import jwt

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from gateway.admin.security import JWT_ALGORITHM, get_jwt_secret
from gateway.database import SessionLocal
from gateway.models import AdminUserModel


bearer_scheme = HTTPBearer(auto_error=False)

VALID_ROLES = {"super_admin", "admin", "viewer"}


def get_optional_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid access token",
            )

        admin_id = int(payload["sub"])

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with SessionLocal() as session:
        admin = (
            session.query(AdminUserModel)
            .filter(
                AdminUserModel.id == admin_id,
                AdminUserModel.is_active.is_(True),
            )
            .first()
        )

        if admin is None:
            raise HTTPException(
                status_code=401,
                detail="Admin account not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return admin


def get_current_admin(
    admin: AdminUserModel | None = Depends(get_optional_current_admin),
):
    if admin is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin


def require_roles(*allowed_roles: str):
    """
    Create a reusable dependency that permits only specified roles.
    """

    if not allowed_roles:
        raise ValueError("At least one role must be specified.")

    invalid_roles = set(allowed_roles) - VALID_ROLES

    if invalid_roles:
        raise ValueError(f"Invalid roles: {invalid_roles}")

    def role_checker(
        admin: AdminUserModel = Depends(get_current_admin),
    ):
        if admin.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action.",
            )

        return admin

    return role_checker


# Read-only access: every valid role.
require_viewer_or_above = require_roles(
    "viewer",
    "admin",
    "super_admin",
)

# Management access: admins and super-admins.
require_admin = require_roles(
    "admin",
    "super_admin",
)

# Highest-level access: super-admin only.
require_super_admin = require_roles("super_admin")