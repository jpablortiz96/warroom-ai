# War Room AI — Bright Data Integration

All five Bright Data products are used in every mission. The Researcher agent selects which product to invoke per data source based on what that source requires to be reached reliably.

---

## 1. MCP Server

**What it does in War Room:**
The Researcher agent uses the Bright Data MCP Server for agentic, programmatic navigation of the live web — following links, extracting content, and drilling into nested pages — without writing bespoke scraping code for each site. The MCP Server exposes the full web as a set of callable tools.

**Which agent uses it:** Researcher (primary), Verifier (source confirmation)

**When it's triggered:**
- Navigating multi-page content (search → result → subpage)
- Sites that require human-like navigation patterns
- Verifying a source URL by fetching and extracting its current content
- Any page where neither the Web Scraper API extractors nor static HTTP suffice

**Endpoint:** `https://mcp.brightdata.com/mcp?token=<API_TOKEN>`

**Screenshot placeholder:** `docs/screenshots/bright-data-mcp-usage.png` _(Day 3)_

---

## 2. Web Scraper API

**What it does in War Room:**
Pulls structured, schema-validated data from 660+ pre-built site extractors. Instead of parsing raw HTML, the Researcher receives clean JSON with typed fields — ideal for LinkedIn company profiles, G2 reviews, Crunchbase funding rounds, Amazon product listings, and Glassdoor ratings.

**Which agent uses it:** Researcher

**When it's triggered:**
- Extracting LinkedIn company data (headcount, hiring velocity, recent posts)
- Pulling G2 or Trustpilot reviews for competitive sentiment analysis
- Fetching Crunchbase funding history and investor signals
- Any site covered by one of Bright Data's 660+ ready-made dataset extractors

**Screenshot placeholder:** `docs/screenshots/bright-data-scraper-api-usage.png` _(Day 3)_

---

## 3. SERP API

**What it does in War Room:**
Executes cross-engine, cross-geography search queries and returns structured organic results, news items, and SERP features. The Researcher uses it for broad signal discovery — finding competitor mentions, pricing changes, hiring surges, regulatory news, and dark web forum discussions — before drilling deeper with other products.

**Which agent uses it:** Researcher (broad discovery pass), Mission Planner (query generation validation)

**When it's triggered:**
- Initial signal sweep at mission start across Google, Bing, and regional engines
- Hiring signal detection (`site:linkedin.com/jobs "Enterprise Sales" "Company Name"`)
- News monitoring for competitor announcements, regulatory filings, incidents
- Dark web and forum signal discovery (`site:reddit.com OR site:pastebin.com`)

**Request shape:**
```python
POST https://api.brightdata.com/request
{
    "zone": "<BRIGHT_DATA_SERP_ZONE>",
    "url": "https://www.google.com/search?q=<query>&brd_json=1",
    "format": "raw"
}
```

**Screenshot placeholder:** `docs/screenshots/bright-data-serp-usage.png` _(Day 3)_

---

## 4. Web Unlocker

**What it does in War Room:**
Provides residential proxy rotation, CAPTCHA solving, and fingerprint management so the Researcher can access pages that block datacenter IPs. Paywalled news sites, protected corporate portals, regionally restricted content, and sites with aggressive anti-bot measures are all reachable via Web Unlocker.

**Which agent uses it:** Researcher

**When it's triggered:**
- News sites that block standard requests (Bloomberg, FT, Reuters)
- Pricing pages that geo-restrict to specific countries
- Pages that return bot-detection challenges to datacenter IPs
- Regulatory filing portals (SEC EDGAR, EU company registries)
- Any URL where a plain `httpx.get()` returns a CAPTCHA or 403

**Screenshot placeholder:** `docs/screenshots/bright-data-unlocker-usage.png` _(Day 3)_

---

## 5. Scraping Browser

**What it does in War Room:**
Renders full JavaScript-heavy pages in a managed remote browser — handling SPAs, infinite-scroll feeds, lazy-loaded content, and client-side data fetching that static HTTP cannot see. The Researcher uses it when the target data only exists after the page's JS has executed.

**Which agent uses it:** Researcher

**When it's triggered:**
- Single-page applications where content is loaded dynamically post-render
- Pricing pages that render server-side but update client-side after login-check
- LinkedIn feeds, Twitter/X timelines, and other infinite-scroll interfaces
- Taking screenshots for visual evidence in the Battle Brief (Day 5)
- Sites requiring multi-step JavaScript interactions (login flows, modal acceptance)

**Screenshot placeholder:** `docs/screenshots/bright-data-browser-usage.png` _(Day 3)_

---

## Product selection logic (Researcher agent)

```
For each source URL in the research plan:

  1. Does Bright Data have a structured extractor for this domain?
     → Yes: Web Scraper API  (clean JSON, no parsing needed)

  2. Is this a broad signal discovery step?
     → Yes: SERP API  (cross-engine, returns organic list)

  3. Does the page require agentic multi-step navigation?
     → Yes: MCP Server  (tool-call based navigation)

  4. Does the page execute meaningful JavaScript before data appears?
     → Yes: Scraping Browser  (full render)

  5. Is the page protected by bot detection, geo-block, or paywall?
     → Yes: Web Unlocker  (residential proxy + CAPTCHA bypass)

  Default: Web Unlocker  (safe fallback for unknown sites)
```

Per-product call counts are logged in `agent_events` (tagged with `bright_data_product`) and aggregated in `briefs.bright_data_calls` for the UI usage panel.
