# War Room AI — Supabase Schema

## Apply the schema

Run `schema.sql` in the Supabase SQL editor when ready (Day 2):

1. Go to your Supabase project → SQL Editor → New query
2. Paste the contents of `schema.sql`
3. Click Run
4. Verify all tables appear in Table Editor

## When to apply

Do **not** apply until Day 2. The schema is complete and reviewed — Day 1 is
local dev only (no Supabase connection required).

## Key design decisions

- `bright_data_product` enum on `agent_events` and `citations` — every Researcher
  tool call is tagged with the exact Bright Data product used. This drives the
  per-mission usage counter panel in the UI.
- `market_move_score` and `confidence_score` are separate columns — the Commander
  can be highly confident in weak evidence (low score, high confidence) or uncertain
  about a strong signal (high score, low confidence).
- `action_pack jsonb` on `briefs` — landing angle, email sequence, CRM payload,
  and risk warning are stored as a flexible JSON object, allowing the UI to render
  each field distinctly.
- RLS is commented out — enable Day 4 when adding Supabase Auth.
