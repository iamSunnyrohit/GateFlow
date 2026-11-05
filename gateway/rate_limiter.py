
import os
import time

from fastapi import Depends, HTTPException, Request
from redis.exceptions import RedisError

from gateway.auth import require_api_key


RATE_LIMIT = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

if RATE_LIMIT <= 0 or WINDOW_SECONDS <= 0:
    raise ValueError("Rate limit and window duration must be positive")


# Atomically increment the counter and set its expiry on the first request.
RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])

if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

local ttl = redis.call('TTL', KEYS[1])

return {current, ttl}
"""


async def enforce_rate_limit(
    request: Request,
    _auth=Depends(require_api_key),
):
    # Browser CORS preflight requests should not consume the API quota.
    if request.method == "OPTIONS":
        return

    api_key_id = getattr(request.state, "api_key_id", None)

    if api_key_id is None:
        raise HTTPException(
            status_code=401,
            detail="API key authentication required",
        )

    now = int(time.time())

    # Fixed 60-second windows aligned to the Unix clock.
    window_number = now // WINDOW_SECONDS
    reset_at = (window_number + 1) * WINDOW_SECONDS
    seconds_until_reset = max(1, reset_at - now)

    redis_key = (
        f"gateflow:rate_limit:{api_key_id}:{window_number}"
    )

    try:
        redis_client = request.app.state.redis

        result = await redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            redis_key,
            seconds_until_reset,
        )

        request_count = int(result[0])

    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Rate limiting service is temporarily unavailable",
            headers={"Retry-After": "5"},
        )

    remaining = max(0, RATE_LIMIT - request_count)

    rate_headers = {
        "X-RateLimit-Limit": str(RATE_LIMIT),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_at),
    }

    # The proxy will copy these headers onto the upstream response.
    request.state.rate_limit_headers = rate_headers

    if request_count > RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again after the current window resets.",
            headers={
                **rate_headers,
                "Retry-After": str(seconds_until_reset),
            },
        )
