from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str = ""

    # Bright Data — shared token + zone names
    bright_data_api_token: str = ""
    bright_data_serp_zone: str = "serp_api"
    bright_data_unlocker_zone: str = "web_unlocker1"
    bright_data_browser_zone: str = "scraping_browser1"

    # Bright Data — Scraping Browser CDP auth
    bright_data_browser_user: str = ""
    bright_data_browser_pass: str = ""

    # Bright Data — Web Scraper API dataset ID (gd_xxxx from dashboard)
    bright_data_scraper_dataset_id: str = ""

    # Bright Data — MCP Server
    bright_data_mcp_url: str = "https://mcp.brightdata.com/mcp"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
