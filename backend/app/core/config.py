from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OzLanka Outdoor Gear"
    database_url: str = "postgresql+psycopg://ozlanka:change-me@db:5432/ozlanka"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "change-me-too"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "change-me-admin"
    fx_api_url: str = "https://open.er-api.com/v6/latest/AUD"
    fx_fallback_aud_lkr: float = 190
    handling_fee_percent: float = 25
    scrape_target_urls: str = "https://www.4wdsupacentre.com.au/media/sitemap_4wdsc.xml"
    scrape_interval_seconds: int = 60 * 60 * 24 * 14
    backend_internal_url: str = "http://backend:8000"
    next_public_app_name: str = "OzLanka Outdoor Gear"
    next_public_handling_fee_default: float = 25


@lru_cache
def get_settings() -> Settings:
    return Settings()
