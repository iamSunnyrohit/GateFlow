
import httpx

from fastapi import Request, HTTPException
from fastapi.responses import Response


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
}


async def forward_request(
    request: Request,
    service_url: str,
    path: str
):
    """
    Forward an incoming client request
    to the appropriate backend service.
    """

    # Build the backend URL
    target_url = f"{service_url.rstrip('/')}/{path.lstrip('/')}"

    # Preserve query parameters
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Filter hop-by-hop request headers
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    body = await request.body()

    try:
        client: httpx.AsyncClient = request.app.state.http_client

        backend_response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )

        response_headers = {
            key: value
            for key, value in backend_response.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
            and key.lower() not in {
                "content-length",
                "content-encoding",
                "date",
                "server",
            }
        }


        return Response(
            content=backend_response.content,
            status_code=backend_response.status_code,
            headers=response_headers,
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Backend service timed out"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Backend service is unavailable"
        )
