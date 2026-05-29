-- Scraper API snapshot cache — avoids re-triggering expensive LinkedIn jobs.
-- Run once in Supabase SQL editor: https://supabase.com/dashboard/project/_/sql

create table if not exists scraper_cache (
    target_url  text        not null,
    dataset_id  text        not null,
    snapshot_id text        not null,
    data        jsonb,
    created_at  timestamptz default now() not null,
    primary key (target_url, dataset_id)
);

-- Cache TTL enforced in application code (24h). This index supports cleanup queries.
create index if not exists scraper_cache_created_at_idx on scraper_cache (created_at);
