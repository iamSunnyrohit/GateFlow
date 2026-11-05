import os
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as redis

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from gateway.config import settings
from gateway.core.proxy import forward_request
from gateway.core.route_registry import route_registry
from gateway.middleware.request_logger import RequestLoggerMiddleware

from gateway.admin.routes import router as admin_router
from gateway.admin.api_keys import router as api_keys_router

from gateway.database import initialize_database
from gateway.rate_limiter import enforce_rate_limit

from gateway.analytics.routes import router as analytics_router
from gateway.admin.auth_routes import router as admin_auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize PostgreSQL and load routes
    initialize_database()

    # Create shared Redis connection
    redis_client = redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )

    # Verify Redis connection
    await redis_client.ping()

    app.state.redis = redis_client

    # Create shared HTTP client
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.REQUEST_TIMEOUT),
        follow_redirects=False,
    )

    print("GateFlow Gateway started successfully")
    print("Redis connection established")

    yield

    # Close connections
    await app.state.http_client.aclose()
    await redis_client.aclose()

    print("GateFlow Gateway stopped")


app = FastAPI(
    title=settings.APP_NAME,
    description="A developer-focused API Gateway",
    version="0.3.0",
    lifespan=lifespan,
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-GateFlow-Latency",
        "X-GateFlow-Status",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)

app.add_middleware(RequestLoggerMiddleware)

# Admin routes
app.include_router(admin_router)
app.include_router(api_keys_router)
app.include_router(analytics_router)
app.include_router(admin_auth_router)


@app.get("/")
async def root():

    return {
        "name": "GateFlow",
        "message": "API Gateway is running",
        "version": "0.3.0",
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "gateflow-gateway",
    }


@app.get("/gateway/routes")
async def get_registered_routes():

    return {
        "total": len(route_registry.list_routes()),
        "routes": route_registry.list_routes(),
    }


async def dispatch_request(request: Request):

    # Get incoming URL path
    incoming_path = request.url.path

    # Find matching backend route
    route = route_registry.resolve(incoming_path)

    if route is None:
        raise HTTPException(
            status_code=404,
            detail="No matching API route found",
        )

    # Validate HTTP method
    if request.method not in route.methods:
        raise HTTPException(
            status_code=405,
            detail="HTTP method not allowed for this route",
            headers={
                "Allow": ", ".join(sorted(route.methods))
            },
        )

    # Rewrite path for backend
    upstream_path = incoming_path

    if route.strip_prefix:

        if incoming_path == route.strip_prefix:
            upstream_path = "/"

        elif incoming_path.startswith(
            route.strip_prefix + "/"
        ):
            upstream_path = incoming_path[
                len(route.strip_prefix):
            ]

    print(
        f"Routing {request.method} {incoming_path} "
        f"-> {route.name} "
        f"({route.service_url}{upstream_path})"
    )

    # Forward request to backend
    upstream_response = await forward_request(
        request=request,
        service_url=route.service_url,
        path=upstream_path,
    )

    # Attach rate-limit headers to upstream response
    rate_limit_headers = getattr(
        request.state,
        "rate_limit_headers",
        {},
    )

    for header, value in rate_limit_headers.items():
        upstream_response.headers[header] = value

    return upstream_response


# API root
@app.api_route(
    "/api",
    methods=[
        "GET", "POST", "PUT", "PATCH",
        "DELETE", "OPTIONS", "HEAD",
    ],
    dependencies=[Depends(enforce_rate_limit)],
)
async def proxy_root(request: Request):

    return await dispatch_request(request)


# Dynamic API routing
@app.api_route(
    "/api/{path:path}",
    methods=[
        "GET", "POST", "PUT", "PATCH",
        "DELETE", "OPTIONS", "HEAD",
    ],
    dependencies=[Depends(enforce_rate_limit)],
)
async def proxy_requests(
    request: Request,
    path: str,
):

    return await dispatch_request(request)
