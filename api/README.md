# War Room AI — Backend API

FastAPI + LangGraph backend for the War Room AI autonomous market intelligence engine.

## Quickstart

```powershell
# 1. Install dependencies
cd api
uv sync

# 2. Configure environment
Copy-Item .env.example .env
# Edit .env — set BRIGHT_DATA_API_TOKEN and zone names at minimum

# 3. Run dev server
uv run uvicorn main:app --reload --port 8000
```

## Verify it works

```powershell
# Health check
Invoke-RestMethod http://localhost:8000/health

# Bright Data smoke test (requires BRIGHT_DATA_API_TOKEN in .env)
Invoke-RestMethod http://localhost:8000/missions/hello
```

## Run tests

```powershell
uv run pytest tests/ -v
```

## Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/missions/hello` | Bright Data reachability test |
| GET | `/missions/{id}/stream` | SSE stream for running mission (Day 2) |

## Zone name verification

Bright Data zone names are account-specific. Check yours at:
**dashboard → Proxies & Scraping → [product] → zone name**

Common defaults: `serp_api`, `web_unlocker1`, `scraping_browser1`
