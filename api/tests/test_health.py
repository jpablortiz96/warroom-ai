import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_health_returns_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "warroom-ai-api"


@pytest.mark.asyncio
async def test_hello_without_token_returns_config_needed(monkeypatch):
    import app.config as cfg
    monkeypatch.setattr(cfg.settings, "bright_data_api_token", "")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/missions/hello")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "config_needed"
