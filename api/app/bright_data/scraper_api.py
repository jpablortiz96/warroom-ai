"""Bright Data Web Scraper API — structured data from 660+ site extractors.

Trigger:  POST https://api.brightdata.com/datasets/v3/trigger
Poll:     GET  https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}
Auth:     Authorization: Bearer <token>

Snapshot lifecycle states:
  building / collecting / digesting → still processing, keep polling
  ready                             → data available at /snapshot/{id}
  failed                            → terminal error

Workflow:
  1. Check cache (scraper_cache table) for recent hit
  2. trigger_collect(dataset_id, inputs) → snapshot_id
  3. get_snapshot(snapshot_id) — polls every 5s up to 150s
  4. On success → write to cache and return data

Used by: Researcher agent — LinkedIn person profiles primarily.
"""

import asyncio
import logging

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

# States that mean "still processing — keep polling".
_PENDING_STATES = {"building", "collecting", "digesting", "running", "pending", "queued"}

log = logging.getLogger("brightdata")


async def trigger_collect(dataset_id: str, inputs: list[dict]) -> str:
    """Trigger a dataset collection. Returns the snapshot_id for polling."""
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
        body = resp.text
        log.warning(
            "brightdata.raw product=web_scraper_api tool=trigger status_code=%d body_first_500=%r",
            resp.status_code, body[:500],
        )
        resp.raise_for_status()
        data = resp.json()
        return data["snapshot_id"]


async def get_snapshot(
    snapshot_id: str,
    format: str = "json",
    max_wait_seconds: int = 150,
    poll_interval: int = 5,
) -> BrightDataResponse:
    """Poll for a snapshot until ready or timeout.

    Handles both HTTP-status-based (202 = pending, 200 = ready) and
    body-field-based (status: "building" / "ready" / "failed") state reporting.
    """
    start = timer()
    url = _SNAPSHOT_URL.format(snapshot_id=snapshot_id)

    while True:
        elapsed = elapsed_ms(start)
        if elapsed > max_wait_seconds * 1000:
            log.warning(
                "brightdata.raw product=web_scraper_api tool=snapshot snapshot_id=%s status=timeout elapsed_ms=%d",
                snapshot_id, elapsed,
            )
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

            body = resp.text
            ms = elapsed_ms(start)

            log.warning(
                "brightdata.raw product=web_scraper_api tool=snapshot snapshot_id=%s status_code=%d elapsed_ms=%d body_first_500=%r",
                snapshot_id, resp.status_code, ms, body[:500],
            )

            # HTTP 202 — still processing regardless of body.
            if resp.status_code == 202:
                await asyncio.sleep(poll_interval)
                continue

            if resp.status_code >= 400:
                return BrightDataResponse(
                    status="failed",
                    product="web_scraper_api",
                    error=f"HTTP {resp.status_code}: {body[:300]}",
                    latency_ms=ms,
                )

            # HTTP 200 — check for body-level status field.
            try:
                data = resp.json()
            except Exception:
                data = None

            if isinstance(data, dict):
                snap_status = str(data.get("status", "")).lower()
                if snap_status in _PENDING_STATES:
                    await asyncio.sleep(poll_interval)
                    continue
                if snap_status == "failed":
                    return BrightDataResponse(
                        status="failed",
                        product="web_scraper_api",
                        error=f"Snapshot failed: {body[:300]}",
                        latency_ms=ms,
                    )

            # Ready — data can be a list or dict.
            if data is None:
                return BrightDataResponse(
                    status="empty",
                    product="web_scraper_api",
                    error=f"Snapshot returned non-JSON: {body[:300]}",
                    latency_ms=ms,
                )

            return BrightDataResponse(
                status="ok",
                product="web_scraper_api",
                data=data,
                latency_ms=ms,
            )

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            import httpx
            err = str(exc)
            if isinstance(exc, httpx.HTTPStatusError):
                err = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            return BrightDataResponse(
                status="failed",
                product="web_scraper_api",
                error=err,
                latency_ms=elapsed_ms(start),
            )


async def collect_and_wait(
    dataset_id: str,
    inputs: list[dict],
    max_wait_seconds: int = 150,
) -> BrightDataResponse:
    """Check cache, then trigger + poll. Writes result to cache on success."""
    from app.db.client import aget_scraper_cache, aset_scraper_cache

    # Cache key is the first input URL (covers LinkedIn person profiles).
    cache_key = inputs[0].get("url", str(inputs)) if inputs else str(inputs)

    # Cache hit?
    cached = await aget_scraper_cache(cache_key, dataset_id)
    if cached:
        log.warning(
            "brightdata.raw product=web_scraper_api tool=cache_hit url=%r snapshot_id=%s",
            cache_key, cached.get("snapshot_id", "unknown"),
        )
        return BrightDataResponse(
            status="ok",
            product="web_scraper_api",
            data=cached["data"],
            latency_ms=0,
        )

    start = timer()
    try:
        snapshot_id = await trigger_collect(dataset_id, inputs)
        result = await get_snapshot(snapshot_id, max_wait_seconds=max_wait_seconds)

        # Write to cache on success.
        if result.ok and result.data:
            try:
                await aset_scraper_cache(cache_key, dataset_id, snapshot_id, result.data)
                log.warning(
                    "brightdata.raw product=web_scraper_api tool=cache_write url=%r snapshot_id=%s",
                    cache_key, snapshot_id,
                )
            except Exception as cache_err:
                log.warning("brightdata: cache write failed: %s", cache_err)

        return result

    except Exception as exc:
        import httpx
        err = str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        return BrightDataResponse(
            status="failed",
            product="web_scraper_api",
            error=err,
            latency_ms=elapsed_ms(start),
        )


async def collect_linkedin_company(company_url: str) -> BrightDataResponse:
    """Convenience wrapper for LinkedIn Company extractor."""
    dataset_id = settings.bright_data_scraper_dataset_id
    if not dataset_id:
        return BrightDataResponse(
            status="failed",
            product="web_scraper_api",
            error="BRIGHT_DATA_SCRAPER_DATASET_ID not set in .env",
        )
    return await collect_and_wait(dataset_id, [{"url": company_url}])
