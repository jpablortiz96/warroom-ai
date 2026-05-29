-- Add Slack webhook URL to mission_schedules for auto-delivery.
-- Run once in Supabase SQL editor: https://supabase.com/dashboard/project/_/sql

alter table mission_schedules
  add column if not exists slack_webhook_url text default null;
