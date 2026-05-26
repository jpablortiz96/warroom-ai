"""Advanced SERP API client — multi-engine, multi-geography. Day 2 implementation."""


async def search_google(query: str, country: str = "us", lang: str = "en", limit: int = 10) -> list[dict]:
    raise NotImplementedError("Day 2")


async def search_bing(query: str, limit: int = 10) -> list[dict]:
    raise NotImplementedError("Day 2")


async def search_news(query: str, days_back: int = 7, limit: int = 10) -> list[dict]:
    raise NotImplementedError("Day 2")
