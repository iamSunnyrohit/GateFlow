from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, text

from gateway.admin.dependencies import (
    get_current_admin,
    get_optional_current_admin,
)
from gateway.admin.security import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)
from gateway.database import SessionLocal
from gateway.models import AdminUserModel


router = APIRouter(
    prefix="/gateway/admin/auth",
    tags=["Admin Authentication"],
)



class AdminRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=12, max_length=128)

    role: Literal["super_admin", "admin", "viewer"] = "admin"


class AdminLoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)




@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_admin(
    data: AdminRegisterRequest,
    current_admin: AdminUserModel | None = Depends(
        get_optional_current_admin
    ),
):
    username = data.username.strip().lower()
    email = data.email.strip().lower()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty",
        )

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=400,
            detail="A valid email address is required",
        )

    with SessionLocal() as session:
        with session.begin():

            # Serialize registrations to prevent two simultaneous
            # requests from both becoming the first super-admin.
            session.execute(
                text("SELECT pg_advisory_xact_lock(734829105)")
            )

            admin_count = (
                session.query(func.count(AdminUserModel.id)).scalar()
                or 0
            )

            if admin_count == 0:
                # First account is always the initial super-admin.
                assigned_role = "super_admin"

            else:
                # After bootstrap, only an existing super-admin
                # may create another admin account.
                if (
                    current_admin is None
                    or current_admin.role != "super_admin"
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Only a super-admin can register additional admins",
                    )

                assigned_role = data.role

            existing_user = session.query(AdminUserModel).filter(
                or_(
                    func.lower(AdminUserModel.username) == username,
                    func.lower(AdminUserModel.email) == email,
                )
            ).first()

            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail="Username or email is already registered",
                )

            admin = AdminUserModel(
                username=username,
                email=email,
                password_hash=hash_password(data.password),
                role=assigned_role,
                is_active=True,
            )

            session.add(admin)
            session.flush()

            result = {
                "message": "Admin account created successfully",
                "admin": {
                    "id": admin.id,
                    "username": admin.username,
                    "email": admin.email,
                    "role": admin.role,
                    "is_active": admin.is_active,
                },
            }

        return result


@router.post("/login")
def login_admin(data: AdminLoginRequest):

    identifier = data.identifier.strip().lower()

    with SessionLocal() as session:
        admin = session.query(AdminUserModel).filter(
            or_(
                func.lower(AdminUserModel.username) == identifier,
                func.lower(AdminUserModel.email) == identifier,
            )
        ).first()

        # Use the same error for nonexistent accounts and bad passwords.
        if admin is None or not verify_password(
            data.password,
            admin.password_hash,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not admin.is_active:
            raise HTTPException(
                status_code=403,
                detail="This admin account is inactive",
            )

        admin.last_login_at = datetime.now(timezone.utc)

        session.commit()

        token = create_access_token(
            admin_id=admin.id,
            role=admin.role,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "admin": {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "role": admin.role,
            },
        }




@router.get("/me")
def get_admin_profile(
    admin: AdminUserModel = Depends(get_current_admin),
):
    return {
        "id": admin.id,
        "username": admin.username,
        "email": admin.email,
        "role": admin.role,
        "is_active": admin.is_active,
        "created_at": admin.created_at,
        "last_login_at": admin.last_login_at,
    }