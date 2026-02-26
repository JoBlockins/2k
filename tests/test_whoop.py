"""Tests for Whoop token storage, client, and sync."""

import json
import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.data.whoop_tokens import is_expired, load_tokens, save_tokens, TOKEN_PATH
from src.data.whoop_client import WhoopAuthError, WhoopClient
from src.data.whoop_sync import sync_whoop
from src.models.wellness import RecoveryMetrics


# ── Token storage tests ──────────────────────────


class TestTokenStorage:
    def test_save_and_load(self, tmp_path, monkeypatch):
        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)

        save_tokens("access123", "refresh456", 3600)

        tokens = load_tokens()
        assert tokens["access_token"] == "access123"
        assert tokens["refresh_token"] == "refresh456"
        assert tokens["expires_at"] > time.time()

    def test_load_missing_file(self, tmp_path, monkeypatch):
        token_file = tmp_path / "nonexistent.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)

        assert load_tokens() is None

    def test_is_expired_fresh_token(self):
        tokens = {"expires_at": time.time() + 3600}
        assert is_expired(tokens) is False

    def test_is_expired_old_token(self):
        tokens = {"expires_at": time.time() - 100}
        assert is_expired(tokens) is True

    def test_is_expired_within_buffer(self):
        tokens = {"expires_at": time.time() + 200}  # within 300s buffer
        assert is_expired(tokens) is True

    def test_file_permissions(self, tmp_path, monkeypatch):
        import os

        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)

        save_tokens("a", "b", 3600)

        mode = os.stat(token_file).st_mode & 0o777
        assert mode == 0o600


# ── Client tests ──────────────────────────


class TestWhoopClient:
    def test_init_raises_without_tokens(self, tmp_path, monkeypatch):
        token_file = tmp_path / "nonexistent.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)

        with pytest.raises(WhoopAuthError, match="No Whoop tokens found"):
            WhoopClient()

    def test_init_with_valid_tokens(self, tmp_path, monkeypatch):
        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)

        save_tokens("access", "refresh", 3600)

        client = WhoopClient()
        assert client._tokens["access_token"] == "access"
        client.close()

    def test_parse_recovery_metrics_basic(self, tmp_path, monkeypatch):
        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)
        save_tokens("access", "refresh", 3600)

        client = WhoopClient()
        recovery = {
            "created_at": "2026-02-10T08:00:00.000Z",
            "score": {
                "resting_heart_rate": 48,
                "hrv_rmssd_milli": 65.5,
                "recovery_score": 82.0,
            },
        }
        metrics = client.parse_recovery_metrics(recovery)

        assert metrics.date == date(2026, 2, 10)
        assert metrics.resting_hr == 48
        assert metrics.hrv_rmssd == 65.5
        assert metrics.whoop_recovery_score == 82.0
        assert metrics.source == "whoop"
        client.close()

    def test_parse_recovery_with_sleep_and_strain(self, tmp_path, monkeypatch):
        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)
        save_tokens("access", "refresh", 3600)

        client = WhoopClient()
        recovery = {
            "created_at": "2026-02-10T08:00:00.000Z",
            "score": {"resting_heart_rate": 50, "recovery_score": 75.0},
        }
        sleep = {
            "score": {
                "total_in_bed_time_milli": 28800000,  # 480 min
                "sleep_performance_percentage": 88.0,
                "total_slow_wave_sleep_time_milli": 5400000,  # 90 min
                "total_rem_sleep_time_milli": 6000000,  # 100 min
                "total_light_sleep_time_milli": 14400000,  # 240 min
                "total_awake_time_milli": 3000000,  # 50 min
            },
        }
        strain = {
            "score": {"strain": 14.5},
        }

        metrics = client.parse_recovery_metrics(recovery, sleep, strain)

        assert metrics.sleep_duration_minutes == 480
        assert metrics.sleep_quality_score == 88.0
        assert metrics.deep_sleep_minutes == 90
        assert metrics.rem_sleep_minutes == 100
        assert metrics.light_sleep_minutes == 240
        assert metrics.awake_minutes == 50
        assert metrics.whoop_strain == 14.5
        client.close()


# ── Sync tests ──────────────────────────


class TestWhoopSync:
    def test_sync_inserts_new_records(self, db, tmp_path, monkeypatch):
        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)
        save_tokens("access", "refresh", 3600)

        mock_recoveries = [
            {
                "created_at": "2026-02-10T08:00:00.000Z",
                "score": {
                    "resting_heart_rate": 48,
                    "hrv_rmssd_milli": 65.5,
                    "recovery_score": 82.0,
                },
            },
        ]

        with patch.object(WhoopClient, "_get_paginated", return_value=mock_recoveries) as mock_get:
            # First call returns recoveries, second/third return empty
            mock_get.side_effect = [mock_recoveries, [], []]
            stats = sync_whoop(db, days=7)

        assert stats["synced"] == 1
        assert stats["errors"] == 0

        record = db.query(RecoveryMetrics).filter(
            RecoveryMetrics.date == date(2026, 2, 10)
        ).first()
        assert record is not None
        assert record.resting_hr == 48
        assert record.source == "whoop"

    def test_sync_updates_existing_whoop_record(self, db, tmp_path, monkeypatch):
        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)
        save_tokens("access", "refresh", 3600)

        # Pre-existing record
        existing = RecoveryMetrics(
            date=date(2026, 2, 10),
            resting_hr=50,
            whoop_recovery_score=70.0,
            source="whoop",
        )
        db.add(existing)
        db.commit()

        mock_recoveries = [
            {
                "created_at": "2026-02-10T08:00:00.000Z",
                "score": {
                    "resting_heart_rate": 48,
                    "recovery_score": 82.0,
                },
            },
        ]

        with patch.object(WhoopClient, "_get_paginated") as mock_get:
            mock_get.side_effect = [mock_recoveries, [], []]
            stats = sync_whoop(db, days=7)

        assert stats["updated"] == 1
        assert stats["synced"] == 0

        record = db.query(RecoveryMetrics).filter(
            RecoveryMetrics.date == date(2026, 2, 10)
        ).first()
        assert record.resting_hr == 48
        assert record.whoop_recovery_score == 82.0

    def test_sync_skips_non_whoop_record(self, db, tmp_path, monkeypatch):
        token_file = tmp_path / ".whoop_tokens.json"
        monkeypatch.setattr("src.data.whoop_tokens.TOKEN_PATH", token_file)
        save_tokens("access", "refresh", 3600)

        # Pre-existing manual record
        existing = RecoveryMetrics(
            date=date(2026, 2, 10),
            resting_hr=50,
            source="manual",
        )
        db.add(existing)
        db.commit()

        mock_recoveries = [
            {
                "created_at": "2026-02-10T08:00:00.000Z",
                "score": {"resting_heart_rate": 48, "recovery_score": 82.0},
            },
        ]

        with patch.object(WhoopClient, "_get_paginated") as mock_get:
            mock_get.side_effect = [mock_recoveries, [], []]
            stats = sync_whoop(db, days=7)

        assert stats["skipped"] == 1

        record = db.query(RecoveryMetrics).filter(
            RecoveryMetrics.date == date(2026, 2, 10)
        ).first()
        assert record.resting_hr == 50  # unchanged
