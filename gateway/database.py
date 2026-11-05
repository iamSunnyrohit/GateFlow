import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://gateflow_user:gateflow_dev_password@localhost:5432/gateflow",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def initialize_database():
    """Create tables, seed default routes, and load saved routes."""

    from gateway.models import (
        APIRouteModel,
        APIKeyModel,
        APIRequestLogModel,
        AdminUserModel,
    )
    from gateway.core.route_registry import Route, route_registry

    Base.metadata.create_all(bind=engine)

    default_routes = [
        Route(
            name="user-service",
            path_prefix="/api/users",
            service_url="http://user-service:8002",
            strip_prefix="/api",
            methods=frozenset({"GET"}),
        ),
        Route(
            name="product-service",
            path_prefix="/api/products",
            service_url="http://product-service:8003",
            strip_prefix="/api",
            methods=frozenset({"GET"}),
        ),
    ]

    with SessionLocal() as session:
        for route in default_routes:
            existing = (
                session.query(APIRouteModel)
                .filter_by(name=route.name)
                .first()
            )

            if existing is None:
                path_conflict = (
                    session.query(APIRouteModel)
                    .filter_by(path_prefix=route.path_prefix)
                    .first()
                )

                if path_conflict is not None:
                    raise RuntimeError(
                        f"Default route path already exists: {route.path_prefix}"
                    )

                session.add(
                    APIRouteModel(
                        name=route.name,
                        path_prefix=route.path_prefix,
                        service_url=route.service_url,
                        strip_prefix=route.strip_prefix,
                        methods=sorted(route.methods),
                    )
                )

        session.commit()

        saved_routes = (
            session.query(APIRouteModel)
            .order_by(APIRouteModel.id)
            .all()
        )

        route_registry.clear()

        for saved in saved_routes:
            route_registry.register(
                Route(
                    name=saved.name,
                    path_prefix=saved.path_prefix,
                    service_url=saved.service_url,
                    strip_prefix=saved.strip_prefix,
                    methods=frozenset(saved.methods),
                )
            )

    print("GateFlow routes loaded from PostgreSQL")
    print("GateFlow analytics database initialized")
