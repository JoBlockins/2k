"""Wyze Scale client for body weight and composition data."""

import json
import time
from datetime import date, datetime
from pathlib import Path

from src.data.config import Config
from src.models.body import BodyWeight

TOKEN_PATH = Path("data/.wyze_token.json")

KG_TO_LBS = 2.20462


class WyzeAuthError(Exception):
    """Raised when Wyze authentication fails."""


class WyzeScaleClient:
    """Client for Wyze Scale data via wyze-sdk."""

    def __init__(self):
        if not Config.WYZE_EMAIL or not Config.WYZE_PASSWORD:
            raise WyzeAuthError(
                "WYZE_EMAIL and WYZE_PASSWORD must be set in .env"
            )

        self._client = self._authenticate()

    def _authenticate(self):
        """Authenticate with Wyze, using cached token when available."""
        from wyze_sdk import Client

        cached = self._load_cached_token()
        if cached and cached.get("access_token"):
            # Try reusing the cached token
            try:
                client = Client(token=cached["access_token"])
                return client
            except Exception:
                pass  # Token expired, re-auth below

        # Fresh login
        kwargs = {
            "email": Config.WYZE_EMAIL,
            "password": Config.WYZE_PASSWORD,
        }
        if Config.WYZE_KEY_ID and Config.WYZE_API_KEY:
            kwargs["key_id"] = Config.WYZE_KEY_ID
            kwargs["api_key"] = Config.WYZE_API_KEY
        if Config.WYZE_TOTP_KEY:
            kwargs["totp_key"] = Config.WYZE_TOTP_KEY

        client = Client(**kwargs)

        # Cache the token for future use
        self._save_token(client._token)

        return client

    def _load_cached_token(self) -> dict | None:
        """Load cached Wyze token from disk."""
        if not TOKEN_PATH.exists():
            return None
        try:
            data = json.loads(TOKEN_PATH.read_text())
            if data.get("expires_at", 0) > time.time():
                return data
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def _save_token(self, token) -> None:
        """Cache Wyze auth token to disk."""
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": str(token),
            "expires_at": time.time() + 86400,  # 24h cache
        }
        TOKEN_PATH.write_text(json.dumps(data))
        TOKEN_PATH.chmod(0o600)

    def get_weight_records(
        self, start_date: date, end_date: date
    ) -> list[BodyWeight]:
        """Fetch scale records and convert to BodyWeight model instances."""
        from wyze_sdk.models.devices import ScaleRecord

        scales = self._client.scales
        records = scales.get_records(
            start_time=datetime.combine(start_date, datetime.min.time()),
            end_time=datetime.combine(end_date, datetime.max.time()),
        )

        results = []
        for rec in records:
            rec_date = self._parse_record_date(rec)
            if rec_date is None or rec_date < start_date or rec_date > end_date:
                continue

            results.append(self._parse_record(rec, rec_date))

        return results

    def _parse_record_date(self, record) -> date | None:
        """Extract date from a ScaleRecord's measure_ts (epoch ms or seconds)."""
        try:
            ts = getattr(record, "measure_ts", None)
            if ts:
                ts = int(ts)
                # Wyze returns milliseconds — convert to seconds if needed
                if ts > 1e12:
                    ts = ts // 1000
                return datetime.fromtimestamp(ts).date()
        except (ValueError, TypeError, OSError):
            pass
        return None

    def _parse_record(self, record, rec_date: date) -> BodyWeight:
        """Convert a Wyze ScaleRecord into a BodyWeight model instance.

        Note: record.weight already returns lbs (SDK converts internally).
        record.muscle is in kg and needs manual conversion.
        """
        weight_lbs = getattr(record, "weight", None) or 0

        body_fat = getattr(record, "body_fat", None)
        muscle_pct = getattr(record, "muscle", None)
        body_water = getattr(record, "body_water", None)

        # Wyze reports muscle as a percentage — convert to lbs
        muscle_lbs = (
            round(weight_lbs * muscle_pct / 100, 2) if muscle_pct else None
        )

        return BodyWeight(
            date=rec_date,
            weight_lbs=round(weight_lbs, 2),
            body_fat_pct=body_fat,
            muscle_mass_lbs=muscle_lbs,
            water_pct=body_water,
            source="wyze",
        )

    def close(self):
        """Clean up resources."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
