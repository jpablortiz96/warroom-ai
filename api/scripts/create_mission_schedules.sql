-- Recurring mission schedules for War Room AI.
-- Run once in Supabase SQL editor: https://supabase.com/dashboard/project/_/sql

create table if not exists mission_schedules (
    id          text        not null primary key default gen_random_uuid()::text,
    target      text        not null,
    mission_type text       not null,
    cron        text        not null,
    label       text,
    active      boolean     default true not null,
    last_run_at timestamptz default null,
    last_mission_id text    default null,
    created_at  timestamptz default now() not null
);

-- Pre-load the Anthropic golden path schedule.
insert into mission_schedules (id, target, mission_type, cron, label, active)
values (
    'preset-anthropic',
    'anthropic.com',
    'account_pulse',
    '0 9 * * 1',
    'Anthropic account_pulse — every Monday 9am UTC',
    true
)
on conflict (id) do nothing;
