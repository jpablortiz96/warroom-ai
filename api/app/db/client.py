"""Supabase client wrapper. Day 2: use for persisting missions and agent_events."""

from supabase import Client, create_client

from app.config import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in api/.env")
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client
