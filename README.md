# War Room AI

![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2-FF6B35?style=flat-square)
![Bright Data](https://img.shields.io/badge/Bright%20Data-5%20products-1A73E8?style=flat-square)
![Claude](https://img.shields.io/badge/Claude-Sonnet-7C3AED?style=flat-square)
![Supabase](https://img.shields.io/badge/Supabase-postgres-3ECF8E?style=flat-square&logo=supabase)
![License](https://img.shields.io/badge/license-MIT-zinc?style=flat-square)

**Autonomous Market Battlefield for Enterprise Decision-Making**

> Deploy 5 autonomous agents that monitor competitors, suppliers, and threats across the live web — then synthesize findings into an Executive Battle Brief with a Market Move Score (0–100) and a Recommended Move: **ATTACK / DEFEND / WAIT / ESCALATE / MONITOR**.

---

## The Problem

Fortune 500 companies have dedicated competitive intelligence teams, real-time data platforms, and armies of analysts watching the market around the clock. Every other company — the 99% — makes strategic decisions with stale data, manual Google searches, and gut instinct. By the time a mid-market GTM team notices a competitor's pricing move, a supplier's financial stress signal, or a credentials leak in the wild, the window to act has already closed. The intelligence exists on the live web. The bottleneck is access, parsing, and synthesis at speed.

## The Solution

War Room AI deploys five specialized autonomous agents against any target — a competitor, a supplier, a market vertical — and returns a concise Executive Battle Brief in minutes, not days. The Mission Planner structures the investigation. The Researcher executes across the live web, using all five Bright Data products to reach every corner of the public internet regardless of bot protection, JavaScript rendering, or geographic restrictions. The Skeptic challenges every finding. The Verifier resolves each challenge with a confidence score 0–100. The Commander synthesizes it all into a Market Move Score, a Recommended Move, and an Action Pack you can execute the same afternoon. Three mission types cover the three dimensions of enterprise risk: competitive intelligence, supply chain, and security surface.

---

## Why This Only Exists with Bright Data

War Room's intelligence quality is a direct function of the breadth and depth of live web data the Researcher agent can reach. No other platform offers the full-stack coverage Bright Data does — and War Room uses all five products on every mission:

| Product | Role in War Room |
|---|---|
| **MCP Server** | Gives the Researcher agentic, programmatic navigation of the live web — tool-calls against pages without writing a line of scraping code |
| **Web Scraper API** | Pulls structured, schema-validated data from 660+ pre-built extractors (LinkedIn, G2, Crunchbase, Amazon, Glassdoor) for clean, parseable intelligence |
| **SERP API** | Cross-engine signal discovery — tracks competitor mentions, news events, pricing changes, and hiring signals across Google, Bing, and regional search engines |
| **Web Unlocker** | Bypasses bot detection, CAPTCHAs, and geo-blocks so the Researcher can reach paywalled portals, protected dashboards, and regionally restricted content |
| **Scraping Browser** | Renders JavaScript-heavy SPAs, infinite-scroll feeds, and login-gated dashboards that static HTTP scrapers cannot access |

A purely API-based agent would be blind to roughly 70% of the live web — the part that sits behind bot protection, JavaScript rendering, or geographic blocks. The combination of all five Bright Data products is what makes War Room's intelligence comprehensive rather than cherry-picked.

---

## Three Flagship Missions = Three Hackathon Tracks

Each mission uses all five Bright Data products. The Researcher agent selects which to invoke per source based on what that site requires to be reached reliably.

| Mission | Hackathon Track | Bright Data Products |
|---|---|---|
| **Account Pulse** | Track 1 — GTM Intelligence | MCP Server · Web Scraper API · SERP API · Web Unlocker · Scraping Browser |
| **Supplier Watch** | Track 2 — Finance & Market Intelligence | Web Scraper API · SERP API · Web Unlocker · Scraping Browser · MCP Server |
| **Threat Surface** | Track 3 — Security & Compliance | Web Unlocker · Scraping Browser · SERP API · MCP Server · Web Scraper API |

### Account Pulse — GTM Intelligence
Monitor competitor pricing, hiring velocity, product launches, and funding events. Know before your sales team does that a competitor just pulled a pricing tier, spiked enterprise hiring, or lost two senior PMs to your company.

### Supplier Watch — Finance & Market Intelligence
Assess supplier financial health, geopolitical risk exposure, regulatory filings, and alternative sourcing options. Surface stress signals before they become supply chain crises.

### Threat Surface — Security & Compliance
Scan for leaked credentials, CVEs in the target's tech stack, dark web mentions, and regulatory compliance gaps. Know what attackers know about a target before they act on it.

---

## The 5 Agents

| Agent | Role | Key Output |
|---|---|---|
| **Mission Planner** | Parses the natural-language target into a structured research plan | Prioritized query list, target sources, risk hypotheses |
| **Researcher** | Executes the plan via all five Bright Data products | Raw findings with source URLs and per-product usage log |
| **Skeptic** | Challenges every finding — what's missing, what's unverified, what could be wrong | Challenge list with confidence impact per finding |
| **Verifier** | Resolves each challenge with additional evidence, assigns confidence 0–100 per claim | Verified claims with source citations |
| **Commander** | Synthesizes the Executive Battle Brief — scores, move, and actions | Market Move Score · Recommended Move · Action Pack |

---

## Sample Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTIVE BATTLE BRIEF · ACCOUNT PULSE
Target: Wix.com · US market
Generated: 2026-05-28 14:32 UTC · Mission #4471
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MARKET MOVE SCORE        82 / 100
RECOMMENDED MOVE         ATTACK
CONFIDENCE               91 / 100

EXECUTIVE SUMMARY
Wix has quietly removed the $29 Business Basic tier from
their US pricing page and shifted enterprise customers to
a custom-quote flow. Job postings for "Enterprise Sales"
in NYC and Austin spiked 340% over 14 days. Two senior
PMs from their commerce team joined Shopify Plus in the
last 21 days. The window to convert mid-market accounts
considering Wix Business is open — 6 to 8 weeks.

FINDINGS
01  Pricing page diff (Web Scraper API + Scraping Browser)
    Business Basic tier removed 2026-05-18 [verified]
02  Hiring signal (SERP API + Web Unlocker)
    42 enterprise sales reqs across NYC, Austin, Toronto
03  Talent flow (MCP Server agentic navigation)
    Two PMs migrated Wix → Shopify Plus [verified]

ACTION PACK
- Landing angle: "Mid-market merchants outgrowing Wix"
- Email sequence: 3-touch, lead with pricing certainty
- CRM payload: 218 accounts tagged 'wix_at_risk'
- Risk warning: monitor for Wix announcement next 14 days

BRIGHT DATA USAGE
- SERP API ........... 14 calls
- Web Scraper API .... 7 calls
- Web Unlocker ....... 6 calls
- Scraping Browser ... 3 calls
- MCP Server ......... 5 calls
- Total .............. 35 calls / mission
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Quickstart

> Requires: Node 20+, pnpm 10+, Python 3.11+, uv 0.11+

```powershell
# Clone
git clone https://github.com/jpablortiz96/warroom-ai.git
cd warroom-ai

# Backend
cd api
uv sync
Copy-Item .env.example .env
# Edit .env: set ANTHROPIC_API_KEY, BRIGHT_DATA_API_TOKEN, zone names
uv run uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd ..\web
pnpm install
pnpm add @supabase/supabase-js eventsource-parser lucide-react sonner zod framer-motion recharts clsx tailwind-merge class-variance-authority
pnpm dlx shadcn@latest add button card badge input textarea separator skeleton --yes
Copy-Item .env.local.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm dev
```

Open `http://localhost:3000` → click **Open War Room** → see live Bright Data SERP results.

---

## Architecture

→ [ARCHITECTURE.md](./ARCHITECTURE.md)

## Bright Data Integration

→ [BRIGHT_DATA_USAGE.md](./BRIGHT_DATA_USAGE.md)

---

## License

MIT

---

Built for the **[Bright Data Web Data UNLOCKED Hackathon](https://brightdata.com/hackathon)** — May 2026
