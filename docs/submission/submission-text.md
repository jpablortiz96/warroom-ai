# War Room AI — Submission Text for Lablab.ai

## Project Title

War Room AI

---

## Short Description (160 chars)

Multi-agent autonomous market battlefield. 5 agents, 5 Bright Data products, 3 mission types — Executive Battle Brief with Market Move Score in under 15 seconds.

---

## Tags

AI Agents, Multi-Agent, Bright Data, MCP, LangGraph, Claude, Enterprise SaaS, Web Intelligence, GTM, Finance, Security, Threat Intelligence, Supplier Risk, FastAPI, Next.js

---

## Long Description (target: 600-800 words)

### The Problem

Every Fortune 500 company has a dedicated competitive intelligence team. Everyone else — the Series B SaaS company, the regional bank, the mid-market manufacturer — makes strategic decisions with Google alerts, stale industry reports, and gut instinct. By the time their GTM team notices a competitor's pricing move, or their procurement team spots a supplier's financial stress signal, or their CISO learns about a credential leak, the window to act has already closed.

Today's options are broken: $120K/yr analyst firms take weeks. Perplexity-style one-shot research returns summaries with no sources or actionable output. Bloomberg-style dashboards show historical data with no synthesis or verdict. None of them produce what a decision-maker actually needs: **a decisive recommendation and an action plan they can execute before lunch.**

### The Solution

War Room AI is a multi-agent autonomous market intelligence platform. Operators point it at any target — a competitor, a supplier, a threat actor — and in under 15 seconds receive an **Executive Battle Brief** containing:

- **Market Move Score** (0–100): a single number that quantifies the urgency and opportunity signal
- **Recommended Move**: ATTACK / DEFEND / ESCALATE / WAIT / MONITOR — a decisive verdict, not a summary
- **Confidence Score** (0–100): based on verified findings across 5 live data sources
- **Action Pack**: specific, sequenced actions for Immediate / This Week / Watch time horizons

The system runs five specialized autonomous agents in sequence: **Planner** (structures the investigation), **Researcher** (executes across the live web via Bright Data), **Skeptic** (adversarially challenges the findings), **Verifier** (resolves challenges with a confidence score), and **Commander** (synthesizes the final brief). The entire pipeline runs in under 15 seconds for a full 5-product, 5-agent mission.

### Why Bright Data is Essential — Not Optional

War Room's intelligence quality is a direct function of the breadth and depth of live web data the Researcher agent can reach. All five Bright Data products are active on every mission:

**SERP API** provides cross-engine signal discovery across Google, Bing, and regional engines — capturing competitor mentions, news events, pricing changes, and hiring signals that would otherwise require separate search engine integrations and residential proxy infrastructure.

**Web Scraper API** provides access to 660+ pre-built, schema-validated extractors for structured data from LinkedIn, Crunchbase, G2, Yahoo Finance, and hundreds more — without building or maintaining a single scraper.

**Web Unlocker** bypasses bot detection, CAPTCHAs, and geographic blocks so the Researcher can access protected press rooms, investor relations pages, trust portals, and government enforcement records that are inaccessible to datacenter IP ranges.

**Scraping Browser** renders JavaScript-heavy SPAs and dynamic pages — including pricing tiers, SPA-gated dashboards, and dynamically loaded news feeds — that static HTTP scrapers cannot access.

**MCP Server** gives the Researcher agentic navigation capability, calling Bright Data tools the same way Claude Desktop would — without building custom MCP scaffolding, subprocess management, or tool routing.

A purely API-based research agent would be blind to roughly 70% of the web's most intelligence-rich content. All five Bright Data products together close that gap.

### The 3 Flagship Missions Cover All 3 Hackathon Tracks

**Account Pulse** (Track 1 — GTM Intelligence) monitors competitor pricing, hiring velocity, product launches, and funding events. Demo target: anthropic.com → DEFEND 72/100, Confidence 78/100.

**Supplier Watch** (Track 2 — Finance & Market Intelligence) assesses supplier financial health, regulatory exposure, and alternative sourcing options. Demo target: boeing.com → DEFEND 72/100, Confidence 78/100.

**Threat Surface** (Track 3 — Security & Compliance) scans for breach history, regulatory enforcement, dark web mentions, and attack surface exposure. Demo target: change.unitedhealthgroup.com → DEFEND 71/100, Confidence 78/100.

These are **real briefs** from the live system, not mocked output.

### Business Model and Market

**Pay-per-mission**: $5/mission. **Growth**: $299/month (100 missions + Slack delivery). **Enterprise**: custom pricing with unlimited missions, custom mission templates, and API access.

**Target ICP**: GTM leaders, supply chain managers, and security teams at Series B–D SaaS companies who need intelligence faster than they can hire analysts. The total addressable market is the $18B competitive intelligence industry, growing 11% YoY, with 200K+ addressable companies in the US alone.

### What's Next

Recurring intelligence delivery (already live via Inngest cron jobs), Slack and email delivery (Slack live, email on roadmap), CRM integrations with HubSpot and Salesforce, a custom mission template builder, and an enterprise self-hosted edition. War Room AI is a product, not a hackathon demo.

---

## Cover Image Specification

Composite image at 1920x1080:
- Left third: Landing page with 3 golden path preset cards
- Center third: Active mission with agent pipeline + Bright Data coverage panel
- Right third: Executive Battle Brief with Market Move Score gauge + DEFEND pill

Title bar at top: "WAR ROOM AI" in monospace + "Powered by Bright Data" badge

Recommended tool: Figma or screenshot composite in Canva

---

## Demo Video Notes

Target runtime: 3 minutes
Script: [docs/video/script.md](../video/script.md)
Recording tool: OBS Studio or Loom
Resolution: 1920x1080 minimum

---

## Links

- GitHub: https://github.com/jpablortiz96/warroom-ai
- Live demo: [to be added Day 5 after deployment]
- Sample briefs: [docs/sample-briefs/](../sample-briefs/)
