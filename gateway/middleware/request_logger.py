import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import run_in_threadpool

from gateway.database import SessionLocal


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("gateflow")


class RequestLoggerMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

        except Exception:
            duration = (time.perf_counter() - start_time) * 1000

            logger.exception(
                "Unhandled request error: %s %s",
                request.method,
                request.url.path,
            )

            await self.record_analytics(
                request=request,
                status_code=500,
                latency_ms=duration,
            )

            raise

        duration = (time.perf_counter() - start_time) * 1000

        logger.info(
            "%s | %s | %s | %.2f ms",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        response.headers["X-GateFlow-Latency"] = f"{duration:.2f}ms"
        response.headers["X-GateFlow-Status"] = str(response.status_code)

        # Record gateway API traffic, not dashboard or health-check traffic.
        if request.url.path == "/api" or request.url.path.startswith("/api/"):
            await self.record_analytics(
                request=request,
                status_code=response.status_code,
                latency_ms=duration,
            )

        return response

    async def record_analytics(
        self,
        request,
        status_code: int,
        latency_ms: float,
    ):
        api_key_id = getattr(request.state, "api_key_id", None)

        try:
            await run_in_threadpool(
                self._save_analytics,
                api_key_id,
                request.method[:10],
                request.url.path[:500],
                status_code,
                latency_ms,
            )

        except Exception:
            # Analytics failures must never break the gateway response.
            logger.exception("Failed to save request analytics")

    @staticmethod
    def _save_analytics(
        api_key_id,
        method,
        path,
        status_code,
        latency_ms,
    ):
        # Import inside the function to avoid circular imports.
        from gateway.models import APIRequestLogModel

        with SessionLocal() as session:
            analytics_record = APIRequestLogModel(
                api_key_id=api_key_id,
                method=method,
                path=path,
                status_code=status_code,
                latency_ms=latency_ms,
            )

            session.add(analytics_record)
            session.commit()
