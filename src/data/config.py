"""Configuration management."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # Claude API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Concept2 API
    CONCEPT2_CLIENT_ID: str = os.getenv("CONCEPT2_CLIENT_ID", "")
    CONCEPT2_CLIENT_SECRET: str = os.getenv("CONCEPT2_CLIENT_SECRET", "")
    CONCEPT2_ACCESS_TOKEN: str = os.getenv("CONCEPT2_ACCESS_TOKEN", "")
    CONCEPT2_API_BASE: str = "https://log.concept2.com/api"

    # Whoop API (v2 — OAuth 2.0)
    WHOOP_CLIENT_ID: str = os.getenv("WHOOP_CLIENT_ID", "")
    WHOOP_CLIENT_SECRET: str = os.getenv("WHOOP_CLIENT_SECRET", "")
    WHOOP_API_BASE: str = "https://api.prod.whoop.com/developer/v2"
    WHOOP_AUTH_URL: str = "https://api.prod.whoop.com/oauth/oauth2/auth"
    WHOOP_TOKEN_URL: str = "https://api.prod.whoop.com/oauth/oauth2/token"
    WHOOP_REDIRECT_URI: str = "http://localhost:8080/callback"
    WHOOP_SCOPES: str = "read:recovery read:sleep read:cycles read:profile offline"

    # Wyze (scale — email/password + API key)
    WYZE_EMAIL: str = os.getenv("WYZE_EMAIL", "")
    WYZE_PASSWORD: str = os.getenv("WYZE_PASSWORD", "")
    WYZE_KEY_ID: str = os.getenv("WYZE_KEY_ID", "")
    WYZE_API_KEY: str = os.getenv("WYZE_API_KEY", "")
    WYZE_TOTP_KEY: str = os.getenv("WYZE_TOTP_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/training.db")

    # Athlete profile
    ATHLETE_WEIGHT_LBS: float = 160.0
    ATHLETE_WEIGHT_KG: float = 72.6
    ATHLETE_MAX_HR: int = 195  # estimate, refine with testing
    ATHLETE_RESTING_HR: int = 50  # baseline, updates from data
    CURRENT_2K_SECONDS: float = 410.0  # 6:50
    GOAL_2K_SECONDS: float = 390.0  # 6:30
    GOAL_DATE: str = "2026-08-01"
