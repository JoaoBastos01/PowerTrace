"""Centralized configuration for the PowerTrace backend."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application settings read from environment variables."""

    default_voltage: int = int(os.getenv("DEFAULT_VOLTAGE", "127"))
    output_dir: str = os.getenv("OUTPUT_DIR", "output")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///powertrace.db")
    secret_key: str = os.getenv("SECRET_KEY", "")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")
    )
    bootstrap_user_email: str | None = os.getenv("BOOTSTRAP_USER_EMAIL")
    bootstrap_user_name: str | None = os.getenv("BOOTSTRAP_USER_NAME")
    bootstrap_user_password: str | None = os.getenv("BOOTSTRAP_USER_PASSWORD")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_generation_attempts: int = int(
        os.getenv("MAX_GENERATION_ATTEMPTS", "3000")
    )

    def validate_security(self) -> None:
        if len(self.secret_key) < 32:
            raise RuntimeError("SECRET_KEY must contain at least 32 characters.")


settings = Settings()
