-- Add sharing support to briefs table.
-- Run once in Supabase SQL editor: https://supabase.com/dashboard/project/_/sql

alter table briefs
  add column if not exists shared_at timestamptz default null;

create index if not exists briefs_shared_at_idx on briefs (shared_at)
  where shared_at is not null;
