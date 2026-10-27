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
    password_reset_minutes: int = 15
    ticket_signing_secret: str | None = None
    ticket_validity_days: int = 30
    booking_hold_minutes: int = 10
    max_active_holds_per_user: int = 3
    max_tickets_per_booking: int = 10
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"
    concierge_timeout_ms: int = 10000
    concierge_history_messages: int = 4
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    upi_payee_id: str = "arupiop@axl"
    upi_payee_name: str = "TixBee"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "bookings@tixbee.local"
    frontend_origin: str = "http://localhost:3000"
    demo_bootstrap_password: str | None = None
    demo_staff_email: str = "staff@tixbee-demo.com"
    demo_admin_email: str = "admin@tixbee-demo.com"
    demo_staff_attraction_slug: str = "visvesvaraya-museum"

    @property
    def ticket_signing_key(self) -> str:
        """Keep ticket signatures separate from login-session signatures."""
        return self.ticket_signing_secret or f"{self.jwt_secret_key}:tickets"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
