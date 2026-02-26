"""Whoop OAuth token file storage."""

import json
import os
import time
from pathlib import Path

TOKEN_PATH = Path(__file__).resolve().parents[2] / "data" / ".whoop_tokens.json"


def load_tokens() -> dict | None:
    """Load tokens from disk. Returns None if file doesn't exist."""
    if not TOKEN_PATH.exists():
        return None
    with open(TOKEN_PATH) as f:
        return json.load(f)


def save_tokens(access_token: str, refresh_token: str, expires_in: int) -> None:
    """Save tokens to disk with expiry timestamp."""
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": time.time() + expires_in,
    }
    with open(TOKEN_PATH, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(TOKEN_PATH, 0o600)


def is_expired(tokens: dict, buffer_seconds: int = 300) -> bool:
    """Check if access token is expired (with 5-minute buffer)."""
    return time.time() >= tokens.get("expires_at", 0) - buffer_seconds
