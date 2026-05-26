-- =============================================================================
-- War Room AI — Supabase Schema
-- Run this in the Supabase SQL editor (Dashboard → SQL Editor → New query)
-- Do NOT apply until Day 2 — schema is defined here for completeness.
-- =============================================================================

-- ── Enum types ────────────────────────────────────────────────────────────────

-- Mission lifecycle
CREATE TYPE mission_status AS ENUM (
    'queued',
    'running',
    'completed',
    'failed'
);

-- The three flagship missions, each mapping to a hackathon track:
--   account_pulse  → Track 1: GTM Intelligence
--   supplier_watch → Track 2: Finance & Market Intelligence
--   threat_surface → Track 3: Security & Compliance
CREATE TYPE mission_type AS ENUM (
    'account_pulse',
    'supplier_watch',
    'threat_surface'
);

-- Commander's recommended strategic move
CREATE TYPE recommended_move AS ENUM (
    'attack',
    'defend',
    'wait',
    'escalate',
    'monitor'
);

-- The five LangGraph agents
CREATE TYPE agent_name AS ENUM (
    'planner',
    'researcher',
    'skeptic',
    'verifier',
    'commander'
);

-- SSE event types emitted during a mission run
CREATE TYPE agent_event_type AS ENUM (
    'started',
    'thinking',
    'tool_call',
    'tool_result',
    'finding',
    'challenge',
    'verified',
    'completed',
    'failed'
);

-- All five Bright Data products used by the Researcher agent.
-- Every tool_call / tool_result event is tagged with the product that was invoked.
-- This drives the per-mission "Bright Data Usage" counter panel in the UI.
CREATE TYPE bright_data_product AS ENUM (
    'mcp_server',
    'web_scraper_api',
    'serp_api',
    'web_unlocker',
    'scraping_browser'
);


-- ── Core tables ───────────────────────────────────────────────────────────────

-- Every initiated War Room operation
CREATE TABLE missions (
    id           uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_type mission_type  NOT NULL,
    status       mission_status NOT NULL DEFAULT 'queued',
    target       text          NOT NULL,
    context      text,
    created_at   timestamptz   NOT NULL DEFAULT now(),
    updated_at   timestamptz   NOT NULL DEFAULT now()
);

-- Live event stream from all five agents.
-- Indexed for SSE replay in chronological order.
CREATE TABLE agent_events (
    id                  uuid             PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id          uuid             NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    agent               agent_name       NOT NULL,
    event_type          agent_event_type NOT NULL,
    message             text             NOT NULL,
    -- Nullable: only set on tool_call and tool_result events from the Researcher.
    -- Powers the per-mission Bright Data usage counter in the UI.
    bright_data_product bright_data_product,
    payload             jsonb,
    created_at          timestamptz      NOT NULL DEFAULT now()
);

-- SSE replay index: fetch all events for a mission ordered by time
CREATE INDEX idx_agent_events_mission_created
    ON agent_events (mission_id, created_at ASC);

-- Executive Battle Brief — one per completed mission
CREATE TABLE briefs (
    id               uuid             PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id       uuid             NOT NULL UNIQUE REFERENCES missions(id) ON DELETE CASCADE,
    -- Market Move Score: composite risk/opportunity rating from the Commander
    market_move_score smallint        NOT NULL CHECK (market_move_score BETWEEN 0 AND 100),
    recommended_move recommended_move NOT NULL,
    -- Confidence score: Verifier's aggregate confidence in the underlying evidence
    confidence_score smallint         NOT NULL CHECK (confidence_score BETWEEN 0 AND 100),
    executive_summary text            NOT NULL,
    -- Structured action pack: landing angle, email copy, CRM payload, risk warning
    action_pack      jsonb            NOT NULL DEFAULT '{}'::jsonb,
    -- Full log of Bright Data product calls made during the mission.
    -- Schema: [{"product": "serp_api", "calls": 14}, ...]
    bright_data_calls jsonb           NOT NULL DEFAULT '[]'::jsonb,
    created_at       timestamptz      NOT NULL DEFAULT now()
);

-- Per-finding citations with confidence scores and source attribution
CREATE TABLE citations (
    id                  uuid             PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id            uuid             NOT NULL REFERENCES briefs(id) ON DELETE CASCADE,
    mission_id          uuid             NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    claim               text             NOT NULL,
    source_url          text             NOT NULL,
    confidence          smallint         NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    agent               agent_name       NOT NULL,
    -- Which Bright Data product was used to retrieve this source
    bright_data_product bright_data_product,
    created_at          timestamptz      NOT NULL DEFAULT now()
);

-- Recurring mission schedules (Day 4 — powered by Inngest)
CREATE TABLE mission_schedules (
    id              uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_type    mission_type  NOT NULL,
    target          text          NOT NULL,
    context         text,
    cron_expression text          NOT NULL,
    enabled         boolean       NOT NULL DEFAULT true,
    last_run_at     timestamptz,
    next_run_at     timestamptz,
    created_at      timestamptz   NOT NULL DEFAULT now()
);

-- Human feedback on battle briefs (Day 5 — RLHF signal)
CREATE TABLE feedback (
    id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id   uuid        NOT NULL REFERENCES briefs(id) ON DELETE CASCADE,
    rating     smallint    CHECK (rating BETWEEN 1 AND 5),
    comment    text,
    created_at timestamptz NOT NULL DEFAULT now()
);


-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX idx_missions_status      ON missions (status);
CREATE INDEX idx_missions_type        ON missions (mission_type);
CREATE INDEX idx_citations_brief      ON citations (brief_id);
CREATE INDEX idx_citations_mission    ON citations (mission_id);


-- ── Row Level Security ────────────────────────────────────────────────────────
-- Enable Day 4 when adding user authentication (Supabase Auth).
-- Policies below are stubs — uncomment and adapt per auth model.

-- ALTER TABLE missions          ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_events      ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE briefs            ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE citations         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE mission_schedules ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE feedback          ENABLE ROW LEVEL SECURITY;

-- Example policy (anon read of completed missions):
-- CREATE POLICY "public read completed missions"
--     ON missions FOR SELECT
--     USING (status = 'completed');

-- Example policy (service role full access):
-- CREATE POLICY "service role full access"
--     ON missions FOR ALL
--     USING (auth.role() = 'service_role');
