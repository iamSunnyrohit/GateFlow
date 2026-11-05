from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    func,
    CheckConstraint
)

from gateway.database import Base

class APIRouteModel(Base):
    __tablename__ = "api_routes"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), unique=True, nullable=False, index=True)
    path_prefix = Column(String(255), unique=True, nullable=False, index=True)
    service_url = Column(String(500), nullable=False)
    strip_prefix = Column(String(255), nullable=False, default="")
    methods = Column(JSON, nullable=False, default=["GET"])


class APIKeyModel(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False, index=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class APIRequestLogModel(Base):
    __tablename__ = "api_request_logs"

    id = Column(Integer, primary_key=True, index=True)

    # References the API key used for the request.
    # Nullable because some requests may not use an API key.
    api_key_id = Column(
        Integer,
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    method = Column(String(10), nullable=False)

    # Store the path only, not query parameters or sensitive data.
    path = Column(String(500), nullable=False, index=True)

    status_code = Column(Integer, nullable=False, index=True)

    latency_ms = Column(Float, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )


class AdminUserModel(Base):
    __tablename__ = "admin_users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin', 'admin', 'viewer')",
            name="check_admin_user_role",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(30),
        nullable=False,
        default="admin",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )