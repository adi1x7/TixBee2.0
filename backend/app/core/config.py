from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TixBee API"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://tixbee:tixbee@db:5432/tixbee_v1"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret_key: str = "change-me-before-deployment"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24
    booking_hold_minutes: int = 10
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.7-flash"
    gemini_fallback_model: str = "gemini-3.6-flash"
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "bookings@tixbee.local"
    frontend_origin: str = "http://localhost:3000"
    demo_bootstrap_password: str | None = None
    demo_staff_email: str = "staff@tixbee.local"
    demo_admin_email: str = "admin@tixbee.local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
