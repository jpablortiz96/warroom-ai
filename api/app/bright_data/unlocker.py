"""Web Unlocker client — bypass bot detection and geo-blocks. Day 2 implementation.

Used by: Researcher agent
When: Fetching pages that block datacenter IPs (paywalls, protected portals, geo-restricted)
"""


async def fetch_unlocked(url: str, country: str | None = None) -> str:
    """Fetch a URL through Web Unlocker and return the page HTML."""
    raise NotImplementedError("Day 2")
