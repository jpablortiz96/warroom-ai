"""Shared types and helpers for all Bright Data product clients."""

import time
from typing import Any

import httpx
from pydantic import BaseModel

from app.config import settings

_REQUEST_ENDPOINT = "https://api.brightdata.com/request"


class BrightDataResponse(BaseModel):
    """Uniform response envelope returned by every Bright Data client function."""

    status: str  # "ok" | "error" | "timeout"
    product: str
    data: Any = None          # parsed result: list[dict] | dict | str
    error: str | None = None
    latency_ms: int = 0

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.bright_data_api_token}",
        "Content-Type": "application/json",
    }


def new_client(timeout: float = 60.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout)


def timer() -> float:
    return time.monotonic()


def elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


async def post_request(
    zone: str,
    url: str,
    product: str,
    extra_body: dict | None = None,
) -> BrightDataResponse:
    """POST to the shared /request gateway (used by SERP and Unlocker)."""
    start = timer()
    body: dict = {"zone": zone, "url": url, "format": "raw"}
    if extra_body:
        body.update(extra_body)
    try:
        async with new_client() as client:
            resp = await client.post(
                _REQUEST_ENDPOINT, headers=auth_headers(), json=body
            )
            ms = elapsed_ms(start)
            resp.raise_for_status()
            return BrightDataResponse(
                status="ok", product=product, data=resp, latency_ms=ms
            )
    except httpx.HTTPStatusError as exc:
        return BrightDataResponse(
            status="error",
            product=product,
            error=f"HTTP {exc.response.status_code}: {exc.response.text[:300]}",
            latency_ms=elapsed_ms(start),
        )
    except Exception as exc:
        return BrightDataResponse(
            status="error",
            product=product,
            error=str(exc),
            latency_ms=elapsed_ms(start),
        )
