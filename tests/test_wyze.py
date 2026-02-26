"""Tests for Wyze scale client and sync."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.data.wyze_client import KG_TO_LBS, WyzeAuthError, WyzeScaleClient
from src.data.wyze_sync import sync_wyze
from src.models.body import BodyWeight


# ── Record parsing / conversion tests ──────────────────────────


class TestWyzeRecordParsing:
    def test_kg_to_lbs_conversion_factor(self):
        """Verify kg→lbs conversion factor is correct (used for muscle)."""
        assert round(72.6 * KG_TO_LBS, 2) == 160.06

    def test_parse_record_weight(self):
        """SDK returns weight in lbs already — verify passthrough."""
        client = _make_client()
        # SDK's .weight property already returns lbs
        record = _make_scale_record(weight=160.06)

        result = client._parse_record(record, date(2026, 2, 10))

        assert result.weight_lbs == 160.06
        assert result.source == "wyze"

    def test_parse_record_body_composition(self):
        """Body fat, muscle (pct→lbs), and water are parsed correctly."""
        client = _make_client()
        record = _make_scale_record(
            weight=160.06, body_fat=12.5, muscle=62.3, body_water=55.0
        )

        result = client._parse_record(record, date(2026, 2, 10))

        assert result.body_fat_pct == 12.5
        assert result.muscle_mass_lbs == round(160.06 * 62.3 / 100, 2)
        assert result.water_pct == 55.0

    def test_parse_record_missing_composition(self):
        """Missing body composition fields come through as None."""
        client = _make_client()
        record = _make_scale_record(weight=160.06)

        result = client._parse_record(record, date(2026, 2, 10))

        assert result.body_fat_pct is None
        assert result.muscle_mass_lbs is None
        assert result.water_pct is None

    def test_parse_record_date_from_epoch_seconds(self):
        """measure_ts epoch timestamp in seconds is parsed to date correctly."""
        client = _make_client()
        ts = int(datetime(2026, 2, 10, 12, 0, 0).timestamp())
        record = _make_scale_record(weight=160.0, measure_ts=ts)

        result = client._parse_record_date(record)

        assert result == date(2026, 2, 10)

    def test_parse_record_date_from_epoch_milliseconds(self):
        """measure_ts epoch timestamp in milliseconds is parsed correctly."""
        client = _make_client()
        ts = int(datetime(2026, 2, 10, 12, 0, 0).timestamp() * 1000)
        record = _make_scale_record(weight=160.0, measure_ts=ts)

        result = client._parse_record_date(record)

        assert result == date(2026, 2, 10)

    def test_init_raises_without_credentials(self, monkeypatch):
        """Client raises WyzeAuthError when credentials are missing."""
        monkeypatch.setattr("src.data.wyze_client.Config.WYZE_EMAIL", "")
        monkeypatch.setattr("src.data.wyze_client.Config.WYZE_PASSWORD", "")

        with pytest.raises(WyzeAuthError, match="WYZE_EMAIL"):
            WyzeScaleClient()


# ── Sync tests ──────────────────────────


class TestWyzeSync:
    def test_sync_inserts_new_records(self, db):
        """New weight records are inserted into the DB."""
        mock_records = [
            BodyWeight(
                date=date(2026, 2, 10),
                weight_lbs=160.0,
                body_fat_pct=12.5,
                source="wyze",
            ),
        ]

        with patch(
            "src.data.wyze_sync.WyzeScaleClient"
        ) as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get_weight_records.return_value = mock_records
            stats = sync_wyze(db, days=7)

        assert stats["synced"] == 1
        assert stats["errors"] == 0

        record = db.query(BodyWeight).filter(
            BodyWeight.date == date(2026, 2, 10)
        ).first()
        assert record is not None
        assert record.weight_lbs == 160.0
        assert record.source == "wyze"

    def test_sync_updates_existing_wyze_record(self, db):
        """Existing Wyze records get updated with new values."""
        existing = BodyWeight(
            date=date(2026, 2, 10),
            weight_lbs=159.0,
            source="wyze",
        )
        db.add(existing)
        db.commit()

        mock_records = [
            BodyWeight(
                date=date(2026, 2, 10),
                weight_lbs=160.0,
                body_fat_pct=12.5,
                source="wyze",
            ),
        ]

        with patch(
            "src.data.wyze_sync.WyzeScaleClient"
        ) as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get_weight_records.return_value = mock_records
            stats = sync_wyze(db, days=7)

        assert stats["updated"] == 1
        assert stats["synced"] == 0

        record = db.query(BodyWeight).filter(
            BodyWeight.date == date(2026, 2, 10)
        ).first()
        assert record.weight_lbs == 160.0
        assert record.body_fat_pct == 12.5

    def test_sync_skips_manual_record(self, db):
        """Manual records are not overwritten by Wyze data."""
        existing = BodyWeight(
            date=date(2026, 2, 10),
            weight_lbs=159.5,
            source="manual",
        )
        db.add(existing)
        db.commit()

        mock_records = [
            BodyWeight(
                date=date(2026, 2, 10),
                weight_lbs=160.0,
                source="wyze",
            ),
        ]

        with patch(
            "src.data.wyze_sync.WyzeScaleClient"
        ) as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get_weight_records.return_value = mock_records
            stats = sync_wyze(db, days=7)

        assert stats["skipped"] == 1

        record = db.query(BodyWeight).filter(
            BodyWeight.date == date(2026, 2, 10)
        ).first()
        assert record.weight_lbs == 159.5  # unchanged
        assert record.source == "manual"  # unchanged

    def test_sync_handles_multiple_records(self, db):
        """Multiple records across different dates sync correctly."""
        mock_records = [
            BodyWeight(date=date(2026, 2, 10), weight_lbs=160.0, source="wyze"),
            BodyWeight(date=date(2026, 2, 11), weight_lbs=159.8, source="wyze"),
        ]

        with patch(
            "src.data.wyze_sync.WyzeScaleClient"
        ) as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get_weight_records.return_value = mock_records
            stats = sync_wyze(db, days=7)

        assert stats["synced"] == 2
        assert db.query(BodyWeight).count() == 2


# ── Helpers ──────────────────────────


def _make_client() -> WyzeScaleClient:
    """Create a WyzeScaleClient without hitting the real API."""
    with patch.object(WyzeScaleClient, "__init__", lambda self: None):
        client = WyzeScaleClient.__new__(WyzeScaleClient)
        return client


def _make_scale_record(
    weight: float = 160.06,
    body_fat: float | None = None,
    muscle: float | None = None,
    body_water: float | None = None,
    measure_ts: int | None = None,
) -> MagicMock:
    """Create a mock ScaleRecord with the given values.

    Note: weight should be in lbs (SDK's .weight property returns lbs).
    muscle is a percentage (converted to lbs using weight).
    """
    record = MagicMock()
    record.weight = weight
    record.body_fat = body_fat
    record.muscle = muscle
    record.body_water = body_water
    record.measure_ts = measure_ts
    return record
