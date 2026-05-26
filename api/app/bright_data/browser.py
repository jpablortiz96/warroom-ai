"""Scraping Browser client — full JS rendering for dynamic pages. Day 2 implementation.

Used by: Researcher agent
When: Sites require JavaScript execution (SPAs, infinite scroll, login-gated dashboards)
"""


async def fetch_rendered(url: str, wait_selector: str | None = None) -> str:
    """Navigate to a URL with the Scraping Browser and return fully rendered HTML."""
    raise NotImplementedError("Day 2")


async def screenshot(url: str) -> bytes:
    """Take a screenshot of a URL via Scraping Browser."""
    raise NotImplementedError("Day 2")
