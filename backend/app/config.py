"""
Application configuration via Pydantic Settings.
Reads from environment variables / .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # App
    app_env: str = "development"
    app_secret_key: str = "change-this-to-a-random-secret"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://merchantmind:merchantmind_dev@localhost:5432/merchantmind"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str = "openai/gpt-oss-20b"

    # Deepgram Voice AI
    deepgram_api_key: str = ""
    deepgram_voice_model: str = "aura-asteria-en"

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # WhatsApp
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""

    # CORS — stored as comma-separated string
    cors_origins_str: str = "http://localhost:3000,http://localhost:80"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(",")]

    @property
    def resolved_database_url(self) -> str:
        import os
        url = self.database_url
        is_docker = os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER")
        if not is_docker and "@postgres:" in url:
            return url.replace("@postgres:5432", "@localhost:5433")
        return url

    @property
    def resolved_redis_url(self) -> str:
        import os
        url = self.redis_url
        is_docker = os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER")
        if not is_docker and "redis://redis:" in url:
            return url.replace("redis://redis:6379", "redis://localhost:6379")
        return url

    model_config = {
        "env_file": [".env", "../.env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
