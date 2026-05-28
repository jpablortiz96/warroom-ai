"""Bright Data Web Scraper API — structured data from 660+ site extractors.

Trigger:  POST https://api.brightdata.com/datasets/v3/trigger
Poll:     GET  https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}
Auth:     Authorization: Bearer <token>

Workflow:
  1. trigger_collect(dataset_id, inputs) → snapshot_id  (async, returns immediately)
  2. get_snapshot(snapshot_id)           → BrightDataResponse  (polls until ready)
  3. collect_and_wait(...)               → convenience wrapper for both steps

Used by: Researcher agent
When:    Target site has a Bright Data pre-built extractor (LinkedIn, G2, Crunchbase, etc.)

TODO(verify-snapshot-status): When the snapshot endpoint returns HTTP 202 the job is
still processing. HTTP 200 with JSON body = data ready. Verify this with a real call.
"""

import asyncio

from app.bright_data.base import (
    BrightDataResponse,
    auth_headers,
    elapsed_ms,
    new_client,
    timer,
)
from app.config import settings

_TRIGGER_URL = "https://api.brightdata.com/datasets/v3/trigger"
_SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"


async def trigger_collect(dataset_id: str, inputs: list[dict]) -> str:
    """Trigger a dataset collection. Returns the snapshot_id for polling.

    Args:
        dataset_id: The gd_xxxx ID from the Bright Data dashboard.
        inputs: List of input objects, e.g. [{"url": "https://linkedin.com/company/..."}]

    Returns:
        snapshot_id string to pass to get_snapshot().
    """
    async with new_client() as client:
        resp = await client.post(
            _TRIGGER_URL,
            params={
                "dataset_id": dataset_id,
                "format": "json",
                "include_errors": "true",
            },
            headers=auth_headers(),
            json=inputs,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["snapshot_id"]


async def get_snapshot(
    snapshot_id: str,
    format: str = "json",
    max_wait_seconds: int = 120,
    poll_interval: int = 5,
) -> BrightDataResponse:
    """Poll for a snapshot until ready or timeout.

    HTTP 202 → still processing, sleep and retry.
    HTTP 200 → data ready, return parsed JSON.
    """
    start = timer()
    url = _SNAPSHOT_URL.format(snapshot_id=snapshot_id)

    while True:
        elapsed = elapsed_ms(start)
        if elapsed > max_wait_seconds * 1000:
            return BrightDataResponse(
                status="timeout",
                product="web_scraper_api",
                error=f"Snapshot {snapshot_id} not ready after {max_wait_seconds}s",
                latency_ms=elapsed,
            )

        try:
            async with new_client(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    params={"format": format},
                    headers=auth_headers(),
                )

            if resp.status_code == 202:
                await asyncio.sleep(poll_interval)
                continue

            resp.raise_for_status()
            data = resp.json()
            return BrightDataResponse(
                status="ok",
                product="web_scraper_api",
                data=data,
                latency_ms=elapsed_ms(start),
            )
        except Exception as exc:
            import httpx
            err = str(exc)
            if isinstance(exc, httpx.HTTPStatusError):
                err = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            return BrightDataResponse(
                status="error",
                product="web_scraper_api",
                error=err,
                latency_ms=elapsed_ms(start),
            )


async def collect_and_wait(
    dataset_id: str,
    inputs: list[dict],
    max_wait_seconds: int = 120,
) -> BrightDataResponse:
    """Trigger a collection and poll until complete. Convenience wrapper."""
    start = timer()
    try:
        snapshot_id = await trigger_collect(dataset_id, inputs)
        return await get_snapshot(
            snapshot_id, max_wait_seconds=max_wait_seconds
        )
    except Exception as exc:
        import httpx
        err = str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        return BrightDataResponse(
            status="error",
            product="web_scraper_api",
            error=err,
            latency_ms=elapsed_ms(start),
        )


async def collect_linkedin_company(company_url: str) -> BrightDataResponse:
    """Convenience wrapper for LinkedIn Company extractor."""
    dataset_id = settings.bright_data_scraper_dataset_id
    if not dataset_id:
        return BrightDataResponse(
            status="error",
            product="web_scraper_api",
            error="BRIGHT_DATA_SCRAPER_DATASET_ID not set in .env",
        )
    return await collect_and_wait(dataset_id, [{"url": company_url}])
