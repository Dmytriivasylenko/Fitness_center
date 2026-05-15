from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # ← add this line
    )

    # Flask
    secret_key: str
    flask_env: str = "production"
    debug: bool = False

    # Database
    database_url: str

    # Celery
    celery_broker_url: str = "amqp://guest:guest@rabbitmq:5672//"
    celery_result_backend: str = "rpc://"

    # Stripe
    stripe_secret_key: str
    stripe_public_key: str

    # Email
    email_password: str = ""
    mail_username: str = ""

    # Uploads
    upload_folder: str = "app/static/uploads"

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        weak_keys = {
            "_343435#y2L_F4Q8z_super_static_key",  # старий захардкоджений ключ
            "change-me",
            "secret",
        }
        if v in weak_keys:
            raise ValueError(
                "SECRET_KEY не змінено! Згенеруй новий:\n"
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY має бути мінімум 32 символи")
        return v

    @field_validator("database_url")
    @classmethod
    def database_url_must_be_postgres(cls, v: str) -> str:
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError("DATABASE_URL має починатись з postgresql://")
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
