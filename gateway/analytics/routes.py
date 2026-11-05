from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Depends
from sqlalchemy import func, case

from gateway.database import SessionLocal
from gateway.models import APIRequestLogModel, APIKeyModel
from gateway.admin.dependencies import require_viewer_or_above

router = APIRouter(
    prefix="/gateway/admin/analytics",
    tags=["Gateway Analytics"],
    dependencies=[Depends(require_viewer_or_above)],
)


@router.get("/overview")
def analytics_overview():
    with SessionLocal() as session:
        total_requests = (
            session.query(func.count(APIRequestLogModel.id)).scalar() or 0
        )

        average_latency = (
            session.query(func.avg(APIRequestLogModel.latency_ms)).scalar() or 0
        )

        successful_requests = (
            session.query(func.count(APIRequestLogModel.id))
            .filter(APIRequestLogModel.status_code.between(200, 299))
            .scalar() or 0
        )

        client_errors = (
            session.query(func.count(APIRequestLogModel.id))
            .filter(APIRequestLogModel.status_code.between(400, 499))
            .scalar() or 0
        )

        server_errors = (
            session.query(func.count(APIRequestLogModel.id))
            .filter(APIRequestLogModel.status_code.between(500, 599))
            .scalar() or 0
        )

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "client_errors": client_errors,
            "server_errors": server_errors,
            "average_latency_ms": round(float(average_latency), 2),
        }


@router.get("/traffic")
def analytics_traffic(
    interval: str = Query(default="minute", pattern="^(minute|hour)$"),
    hours: int = Query(default=24, ge=1, le=168),
):
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    # Use PostgreSQL date_trunc with a validated interval.
    with SessionLocal() as session:
        bucket = func.date_trunc(interval, APIRequestLogModel.created_at)

        rows = (
            session.query(
                bucket.label("time"),
                func.count(APIRequestLogModel.id).label("requests"),
            )
            .filter(APIRequestLogModel.created_at >= start_time)
            .group_by(bucket)
            .order_by(bucket)
            .all()
        )

        return {
            "interval": interval,
            "hours": hours,
            "data": [
                {
                    "time": row.time.isoformat(),
                    "requests": row.requests,
                }
                for row in rows
            ],
        }


@router.get("/endpoints")
def analytics_endpoints(
    limit: int = Query(default=10, ge=1, le=100),
):
    with SessionLocal() as session:
        rows = (
            session.query(
                APIRequestLogModel.method,
                APIRequestLogModel.path,
                func.count(APIRequestLogModel.id).label("requests"),
                func.avg(APIRequestLogModel.latency_ms).label("average_latency"),
            )
            .group_by(
                APIRequestLogModel.method,
                APIRequestLogModel.path,
            )
            .order_by(func.count(APIRequestLogModel.id).desc())
            .limit(limit)
            .all()
        )

        return {
            "endpoints": [
                {
                    "method": row.method,
                    "path": row.path,
                    "requests": row.requests,
                    "average_latency_ms": round(float(row.average_latency), 2),
                }
                for row in rows
            ],
        }


@router.get("/api-keys")
def analytics_api_keys(
    limit: int = Query(default=10, ge=1, le=100),
):
    with SessionLocal() as session:
        rows = (
            session.query(
                APIKeyModel.id,
                APIKeyModel.name,
                APIKeyModel.key_prefix,
                APIKeyModel.is_active,
                func.count(APIRequestLogModel.id).label("requests"),
                func.avg(APIRequestLogModel.latency_ms).label("average_latency"),
            )
            .outerjoin(
                APIRequestLogModel,
                APIKeyModel.id == APIRequestLogModel.api_key_id,
            )
            .group_by(
                APIKeyModel.id,
                APIKeyModel.name,
                APIKeyModel.key_prefix,
                APIKeyModel.is_active,
            )
            .order_by(func.count(APIRequestLogModel.id).desc())
            .limit(limit)
            .all()
        )

        return {
            "api_keys": [
                {
                    "id": row.id,
                    "name": row.name,
                    "key_prefix": row.key_prefix,
                    "is_active": row.is_active,
                    "requests": row.requests,
                    "average_latency_ms": (
                        round(float(row.average_latency), 2)
                        if row.average_latency is not None
                        else 0
                    ),
                }
                for row in rows
            ],
        }


@router.get("/status-codes")
def analytics_status_codes():
    with SessionLocal() as session:
        rows = (
            session.query(
                APIRequestLogModel.status_code,
                func.count(APIRequestLogModel.id).label("requests"),
            )
            .group_by(APIRequestLogModel.status_code)
            .order_by(APIRequestLogModel.status_code)
            .all()
        )

        return {
            "status_codes": [
                {
                    "status_code": row.status_code,
                    "requests": row.requests,
                }
                for row in rows
            ],
        }
