"""Whoop API v2 client with OAuth token management."""

from datetime import date, datetime

import httpx

from src.data.config import Config
from src.data.whoop_tokens import is_expired, load_tokens, save_tokens
from src.models.wellness import RecoveryMetrics


class WhoopAuthError(Exception):
    """Raised when Whoop tokens are missing or authorization fails."""


class WhoopClient:
    """Client for the Whoop Developer API v2 with auto-refreshing tokens."""

    def __init__(self):
        tokens = load_tokens()
        if not tokens:
            raise WhoopAuthError(
                "No Whoop tokens found. Run: python -m scripts.whoop_auth"
            )
        self._tokens = tokens
        self._client = httpx.Client(base_url=Config.WHOOP_API_BASE, timeout=30.0)

    def _ensure_valid_token(self) -> None:
        """Refresh access token if expired."""
        if is_expired(self._tokens):
            if not self._tokens.get("refresh_token"):
                raise WhoopAuthError(
                    "Access token expired and no refresh token available. "
                    "Re-run: python -m scripts.whoop_auth"
                )
            self._refresh_token()

    def _refresh_token(self) -> None:
        """Exchange refresh token for a new access/refresh pair."""
        response = httpx.post(
            Config.WHOOP_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._tokens["refresh_token"],
                "client_id": Config.WHOOP_CLIENT_ID,
                "client_secret": Config.WHOOP_CLIENT_SECRET,
                "scope": Config.WHOOP_SCOPES,
            },
        )
        if response.status_code != 200:
            raise WhoopAuthError(
                f"Token refresh failed ({response.status_code}): {response.text}. "
                "Re-run: python -m scripts.whoop_auth"
            )
        data = response.json()
        save_tokens(data["access_token"], data["refresh_token"], data["expires_in"])
        self._tokens = {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": self._tokens.get("expires_at", 0),
        }
        # Reload to get correct expires_at from save
        self._tokens = load_tokens()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._tokens['access_token']}"}

    def _get_paginated(self, path: str, params: dict | None = None) -> list[dict]:
        """Fetch all pages from a paginated v2 endpoint."""
        self._ensure_valid_token()
        params = dict(params or {})
        all_records = []

        while True:
            response = self._client.get(path, params=params, headers=self._headers())
            response.raise_for_status()
            body = response.json()
            all_records.extend(body.get("records", []))

            next_token = body.get("next_token")
            if not next_token:
                break
            params["nextToken"] = next_token

        return all_records

    def get_recovery(self, start_date: date, end_date: date | None = None) -> list[dict]:
        """Fetch recovery data for a date range."""
        params = {"start": f"{start_date}T00:00:00.000Z"}
        if end_date:
            params["end"] = f"{end_date}T23:59:59.999Z"
        return self._get_paginated("/recovery", params)

    def get_sleep(self, start_date: date, end_date: date | None = None) -> list[dict]:
        """Fetch sleep data for a date range."""
        params = {"start": f"{start_date}T00:00:00.000Z"}
        if end_date:
            params["end"] = f"{end_date}T23:59:59.999Z"
        return self._get_paginated("/activity/sleep", params)

    def get_cycles(self, start_date: date, end_date: date | None = None) -> list[dict]:
        """Fetch physiological cycle (strain) data."""
        params = {"start": f"{start_date}T00:00:00.000Z"}
        if end_date:
            params["end"] = f"{end_date}T23:59:59.999Z"
        return self._get_paginated("/cycle", params)

    def parse_recovery_metrics(
        self,
        recovery: dict,
        sleep: dict | None = None,
        strain: dict | None = None,
    ) -> RecoveryMetrics:
        """Convert Whoop API v2 data into a RecoveryMetrics model instance."""
        score = recovery.get("score", {})
        sleep_data = sleep.get("score", {}) if sleep else {}
        strain_data = strain.get("score", {}) if strain else {}

        rec_date = datetime.fromisoformat(
            recovery.get("created_at", "").replace("Z", "+00:00")
        ).date()

        return RecoveryMetrics(
            date=rec_date,
            resting_hr=int(score.get("resting_heart_rate", 0)) or None,
            hrv_rmssd=score.get("hrv_rmssd_milli"),
            sleep_duration_minutes=(
                int(sleep_data.get("total_in_bed_time_milli", 0) / 60000)
                if sleep_data.get("total_in_bed_time_milli")
                else None
            ),
            sleep_quality_score=sleep_data.get("sleep_performance_percentage"),
            deep_sleep_minutes=(
                int(sleep_data.get("total_slow_wave_sleep_time_milli", 0) / 60000)
                if sleep_data.get("total_slow_wave_sleep_time_milli")
                else None
            ),
            rem_sleep_minutes=(
                int(sleep_data.get("total_rem_sleep_time_milli", 0) / 60000)
                if sleep_data.get("total_rem_sleep_time_milli")
                else None
            ),
            light_sleep_minutes=(
                int(sleep_data.get("total_light_sleep_time_milli", 0) / 60000)
                if sleep_data.get("total_light_sleep_time_milli")
                else None
            ),
            awake_minutes=(
                int(sleep_data.get("total_awake_time_milli", 0) / 60000)
                if sleep_data.get("total_awake_time_milli")
                else None
            ),
            whoop_recovery_score=score.get("recovery_score"),
            whoop_strain=strain_data.get("strain") if strain_data else None,
            source="whoop",
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
