from __future__ import annotations
from typing import List, Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic.functional_validators import field_validator


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "Fashion Store API"
    ENV: Literal["dev", "prod"] = "prod"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"  
    API_PREFIX: str = "api"
    API_VERSION: str = "v1"

    # --- DB (Postgres only) ---
    SQLALCHEMY_DATABASE_URI: str = ""
    ALEMBIC_DATABASE_URI: Optional[str] = None

    # --- Auth ---
    JWT_SECRET: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    RESET_TOKEN_EXPIRE_MINUTES: int = 5
    PASSWORD_MIN_LEN: int = 10

    # --- CORS ---
    CORS_ORIGINS: str = ""

    # --- Payment Services ---
    MOMO_API_KEY: str = ""
    MOMO_SECRET_KEY: str = ""
    ZALOPAY_APP_ID: str = ""
    ZALOPAY_KEY1: str = ""
    ZALOPAY_KEY2: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return (v or "INFO").upper()

    @field_validator("SQLALCHEMY_DATABASE_URI", "JWT_SECRET")
    @classmethod
    def _must_not_be_empty(cls, v: str, info):
        if not v:
            raise ValueError(f"{info.field_name} is required (set it in .env)")
        return v


    @property
    def is_dev(self) -> bool:
        return self.ENV == "dev"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if self.CORS_ORIGINS]


settings = Settings()
