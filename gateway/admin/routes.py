from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from gateway.database import SessionLocal
from gateway.models import APIRouteModel
from gateway.core.route_registry import Route, route_registry
from gateway.admin.dependencies import (
    require_admin,
    require_viewer_or_above,
)

router = APIRouter(
    prefix="/gateway/admin",
    tags=["Route Management"],
)


class RoutePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    path_prefix: str = Field(min_length=1, max_length=255)
    service_url: str = Field(min_length=1, max_length=500)
    strip_prefix: str = Field(default="", max_length=255)
    methods: list[str] = Field(default_factory=lambda: ["GET"])


def build_route(payload: RoutePayload) -> Route:
    return Route(
        name=payload.name.strip(),
        path_prefix=payload.path_prefix.strip(),
        service_url=payload.service_url.strip().rstrip("/"),
        strip_prefix=payload.strip_prefix.strip().rstrip("/"),
        methods=frozenset(
            method.strip().upper()
            for method in payload.methods
        ),
    )


def route_to_dict(route) -> dict:
    return {
        "name": route.name,
        "path_prefix": route.path_prefix,
        "service_url": route.service_url,
        "strip_prefix": route.strip_prefix,
        "methods": sorted(route.methods),
    }


def model_to_dict(route) -> dict:
    return {
        "name": route.name,
        "path_prefix": route.path_prefix,
        "service_url": route.service_url,
        "strip_prefix": route.strip_prefix,
        "methods": sorted(route.methods),
    }


@router.get("/routes")
def list_routes(    current_admin=Depends(require_viewer_or_above), ):

    with SessionLocal() as session:
        routes = (
            session.query(APIRouteModel)
            .order_by(APIRouteModel.id)
            .all()
        )

        return {
            "total": len(routes),
            "routes": [model_to_dict(route) for route in routes],
        }


@router.post("/routes", status_code=201)
def create_route(payload: RoutePayload , current_admin=Depends(require_admin),):

    route = build_route(payload)

    # Validate route configuration before saving.
    try:
        route_registry._validate(route)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    with SessionLocal() as session:

        try:
            existing_name = (
                session.query(APIRouteModel)
                .filter_by(name=route.name)
                .first()
            )

            existing_path = (
                session.query(APIRouteModel)
                .filter_by(path_prefix=route.path_prefix)
                .first()
            )

            if existing_name or existing_path:
                raise HTTPException(
                    status_code=409,
                    detail="Route name or path already exists",
                )

            db_route = APIRouteModel(
                name=route.name,
                path_prefix=route.path_prefix,
                service_url=route.service_url,
                strip_prefix=route.strip_prefix,
                methods=sorted(route.methods),
            )

            session.add(db_route)
            session.commit()

        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Route name or path already exists",
            )

    route_registry.register(route)

    return {
        "message": "Route registered and saved successfully",
        "route": route_to_dict(route),
    }


@router.put("/routes/{name}")
def update_route(name: str, payload: RoutePayload):

    route = build_route(payload)

    if route.name != name:
        raise HTTPException(
            status_code=400,
            detail="Route name cannot be changed",
        )

    try:
        route_registry._validate(route)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    with SessionLocal() as session:

        db_route = (
            session.query(APIRouteModel)
            .filter_by(name=name)
            .first()
        )

        if db_route is None:
            raise HTTPException(
                status_code=404,
                detail="Route not found",
            )

        path_conflict = (
            session.query(APIRouteModel)
            .filter(
                APIRouteModel.path_prefix == route.path_prefix,
                APIRouteModel.name != name,
            )
            .first()
        )

        if path_conflict:
            raise HTTPException(
                status_code=409,
                detail="Path prefix already exists",
            )

        db_route.path_prefix = route.path_prefix
        db_route.service_url = route.service_url
        db_route.strip_prefix = route.strip_prefix
        db_route.methods = sorted(route.methods)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Route configuration conflicts with an existing route",
            )

    route_registry.update(name, route)

    return {
        "message": "Route updated and saved successfully",
        "route": route_to_dict(route),
    }


@router.delete("/routes/{name}")
def delete_route(name: str,current_admin=Depends(require_admin),):

    with SessionLocal() as session:

        db_route = (
            session.query(APIRouteModel)
            .filter_by(name=name)
            .first()
        )

        if db_route is None:
            raise HTTPException(
                status_code=404,
                detail="Route not found",
            )

        deleted_route = model_to_dict(db_route)

        session.delete(db_route)
        session.commit()

    route_registry.remove(name)

    return {
        "message": "Route deleted successfully",
        "route": deleted_route,
    }
