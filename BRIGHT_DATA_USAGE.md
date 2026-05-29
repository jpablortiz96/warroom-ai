# Bright Data Integration — War Room AI

This document details how War Room AI uses all five Bright Data products on every mission, why each product is necessary, and what evidence demonstrates live usage.

---

## Product Coverage Summary

| Product | API Module | Tool Name | Usage Per Mission | Status Check |
|---------|-----------|-----------|-------------------|-------------|
| SERP API | `bright_data/serp.py` | `serp_search`, `serp_news` | 1–2 calls | Live counter in BD panel |
| Web Scraper API | `bright_data/scraper_api.py` | `scraper_linkedin` | 1 call (cached after first) | 24h Supabase cache |
| Web Unlocker | `bright_data/unlocker.py` | `unlocker_fetch` | 1 call | Live counter in BD panel |
| Scraping Browser | `bright_data/browser.py` | `browser_render` | 1 call | Live counter in BD panel |
| MCP Server | `bright_data/mcp_client.py` | `mcp_search`, `mcp_scrape` | 1 call | Live counter in BD panel |

---

## 1 — SERP API

**What we use it for:** Cross-engine competitive signal discovery. The Planner assigns `serp_search` and `serp_news` steps that query Google for news events, pricing changes, hiring signals, breach reports, and regulatory actions. SERP API returns structured organic results with title, description, and URL — clean input for the Researcher's findings corpus.

**Why SERP API specifically:**
- Residential proxy backbone avoids the bot blocks that hit datacenter IP SERP scrapers
- Structured JSON response eliminates HTML parsing — the Researcher gets clean results immediately
- `serp_news` variant surfaces time-sensitive events that organic results would bury

**Configuration:** `BRIGHT_DATA_SERP_ZONE` in `api/.env`

**Code:** [`api/app/bright_data/serp.py`](https://github.com/jpablortiz96/warroom-ai/blob/main/api/app/bright_data/serp.py)

**Screenshot placeholder:**
![SERP API in action](https://github.com/jpablortiz96/warroom-ai/raw/main/docs/screenshots/bd-serp-api.png)
*SERP API results card in the Bright Data Coverage panel: call count, latency, last query sent.*

---

## 2 — Web Scraper API

**What we use it for:** Structured LinkedIn person profile extraction for CEO/founder intelligence. The Planner identifies the current CEO's LinkedIn URL (from a verified hardcoded list or LLM knowledge), and the Researcher calls `collect_and_wait()` to trigger a Bright Data dataset snapshot and poll for results.

**Why Web Scraper API specifically:**
- LinkedIn is unreachable with standard HTTP scraping — the pre-built LinkedIn extractor handles authentication, anti-bot, and data normalization
- The 660+ pre-built extractors mean zero engineering to add new structured sources (Crunchbase, G2, SEC EDGAR are all available)
- Snapshot-based async model matches LinkedIn's 1–3 minute collection window without blocking the mission

**Caching:** Snapshots are cached in `scraper_cache` (Supabase) for 24 hours. A repeat mission on the same target returns the cached profile in 0ms instead of triggering a new snapshot.

**Configuration:** `BRIGHT_DATA_SCRAPER_DATASET_ID` in `api/.env`

**Code:** [`api/app/bright_data/scraper_api.py`](https://github.com/jpablortiz96/warroom-ai/blob/main/api/app/bright_data/scraper_api.py)

**Screenshot placeholder:**
![Scraper API in action](https://github.com/jpablortiz96/warroom-ai/raw/main/docs/screenshots/bd-scraper-api.png)
*Web Scraper API card showing 1 call, 0ms latency (cache hit) or 45–90s (live snapshot).*

---

## 3 — Web Unlocker

**What we use it for:** Bypassing bot protection on press rooms, investor relations pages, trust portals, and government enforcement records. For `supplier_watch` missions, this reaches IR pages at `investors.boeing.com`. For `threat_surface` missions, it reaches regulatory enforcement databases and company security disclosure pages.

**Why Web Unlocker specifically:**
- The highest-value intelligence sources are behind the strictest bot protection — IR pages, government portals, and trust/security pages are actively defended
- Web Unlocker's residential proxy rotation and browser fingerprinting bypass this without requiring per-site configuration
- Returns raw HTML which `markdownify` converts to clean Markdown for LLM consumption

**Configuration:** `BRIGHT_DATA_UNLOCKER_ZONE` in `api/.env`

**Code:** [`api/app/bright_data/unlocker.py`](https://github.com/jpablortiz96/warroom-ai/blob/main/api/app/bright_data/unlocker.py)

**Screenshot placeholder:**
![Web Unlocker in action](https://github.com/jpablortiz96/warroom-ai/raw/main/docs/screenshots/bd-web-unlocker.png)
*Web Unlocker card: call count, latency (~6–15s for protected pages), last URL fetched.*

---

## 4 — Scraping Browser

**What we use it for:** Rendering JavaScript-heavy pages that static HTTP fetchers cannot access. For `account_pulse` missions, this renders the target's `/pricing` page — almost always a React SPA with dynamic tier loading. For `supplier_watch`, it renders IR pages with JS-loaded financial calendars. For `threat_surface`, it renders trust/security pages with dynamically loaded content.

**Why Scraping Browser specifically:**
- Uses Playwright CDP over WSS to connect to Bright Data's managed browser fleet — no local browser process, no anti-bot arms race
- Uses `asyncio.to_thread` to wrap the synchronous Playwright API safely on Windows uvicorn event loops (avoids `NotImplementedError` from async Playwright on Windows)
- Returns rendered HTML which `markdownify` strips to clean Markdown

**Configuration:** `BRIGHT_DATA_BROWSER_USER` and `BRIGHT_DATA_BROWSER_PASS` in `api/.env`

**Code:** [`api/app/bright_data/browser.py`](https://github.com/jpablortiz96/warroom-ai/blob/main/api/app/bright_data/browser.py)

**Screenshot placeholder:**
![Scraping Browser in action](https://github.com/jpablortiz96/warroom-ai/raw/main/docs/screenshots/bd-scraping-browser.png)
*Scraping Browser card: call count, latency (~9–25s for full JS render), last URL rendered.*

---

## 5 — MCP Server

**What we use it for:** Agentic navigation for unstructured exploration tasks. The Researcher calls `mcp_client.search()` and `mcp_client.scrape_markdown()` to send queries through Bright Data's MCP server — the same tool surface Claude Desktop exposes. Used for structured intelligence searches that don't fit a specific pre-built extractor.

**Why MCP Server specifically:**
- Native Claude integration — the Researcher calls Bright Data tools the same way Claude Desktop would, via the `mcp` Python SDK over stdio transport (`npx @brightdata/mcp`)
- `scrape_as_markdown` returns any page as clean Markdown without writing HTML parsing code
- `search_engine` provides a natural-language search interface over Bright Data's SERP infrastructure with a different latency/format tradeoff than the direct SERP API

**Configuration:** `BRIGHT_DATA_API_TOKEN` in `api/.env` (shared with other products)

**Code:** [`api/app/bright_data/mcp_client.py`](https://github.com/jpablortiz96/warroom-ai/blob/main/api/app/bright_data/mcp_client.py)

**Screenshot placeholder:**
![MCP Server in action](https://github.com/jpablortiz96/warroom-ai/raw/main/docs/screenshots/bd-mcp-server.png)
*MCP Server card: call count, latency (~8–20s including npx subprocess startup), last search query.*

---

## The Coverage Panel — Live Proof

Every active mission renders the Bright Data Coverage panel in the War Room Console. Five product cards, each showing:

- **Icon + label** — product identity (Search, Globe, ShieldCheck, FileText, Monitor icons from Lucide)
- **Call count** — large prominent number updated in real time as the Researcher fires each step
- **Cumulative latency** — total seconds contributed by this product to the mission wall time
- **Last goal** — the step goal that used this product, with full tooltip on hover
- **Status dot** — green (ok), amber (empty), red (failed/timeout)

The panel updates via SSE events. Every `tool_call` event increments the counter; every `tool_result` event updates latency and status.

![Full Coverage Panel](https://github.com/jpablortiz96/warroom-ai/raw/main/docs/screenshots/final-04-bright-data-panel.png)

---

## Raw Response Logging

Every Bright Data client emits a `WARNING`-level log line per call for diagnostics. Start the server with `--log-level warning` to see:

```
brightdata.raw product=serp_api tool=serp_search status_code=200 latency_ms=4231 body_first_500='...'
brightdata.raw product=web_unlocker tool=unlocker_fetch status_code=200 latency_ms=8710 body_first_500='...'
brightdata.raw product=mcp_server tool=search_engine latency_ms=12400 result_len=3841 result_first_500='...'
brightdata.raw product=web_scraper_api tool=trigger status_code=200 body_first_500='{"snapshot_id":"..."}'
brightdata.raw product=scraping_browser tool=browser_render latency_ms=9380 html_len=84210 html_first_500='...'
```

---

## Account Usage Reference

Hackathon development account: ~$0.27 spent across 5 days and hundreds of test missions. All zones active, $256+ credit remaining.

Production cost estimate per 6-call mission: ~$0.048 Bright Data. Full unit economics in [README.md](https://github.com/jpablortiz96/warroom-ai/blob/main/README.md).
