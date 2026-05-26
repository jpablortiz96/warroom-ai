"""Web Scraper API client — 660+ structured site extractors. Day 2 implementation.

Used by: Researcher agent
When: Extracting structured data from known sites (LinkedIn, Crunchbase, G2, etc.)
"""


async def scrape_dataset(dataset_id: str, params: dict) -> list[dict]:
    raise NotImplementedError("Day 2")


async def scrape_linkedin_company(company_url: str) -> dict:
    raise NotImplementedError("Day 2")


async def scrape_g2_reviews(product_slug: str, limit: int = 20) -> list[dict]:
    raise NotImplementedError("Day 2")
