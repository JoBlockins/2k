"""Concept2 Logbook API client for importing erg workout data."""

from datetime import date, datetime

import httpx

from src.data.config import Config
from src.models.workout import Workout, WorkoutInterval


class Concept2Client:
    """Client for the Concept2 Online Logbook API."""

    def __init__(self, access_token: str | None = None):
        self.base_url = Config.CONCEPT2_API_BASE
        self.access_token = access_token or Config.CONCEPT2_ACCESS_TOKEN
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=30.0,
        )

    def get_results(self, from_date: date | None = None, to_date: date | None = None) -> list[dict]:
        """Fetch workout results from the Concept2 logbook."""
        params = {"type": "rower"}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()

        response = self._client.get("/users/me/results", params=params)
        response.raise_for_status()
        return response.json().get("data", [])

    def get_result_detail(self, result_id: str) -> dict:
        """Fetch detailed data for a single workout."""
        response = self._client.get(f"/users/me/results/{result_id}")
        response.raise_for_status()
        return response.json().get("data", {})

    def parse_workout(self, raw: dict) -> Workout:
        """Convert a Concept2 API result into a Workout model."""
        workout_date = datetime.fromisoformat(raw.get("date", "")).date()

        # Determine workout type from Concept2 data
        workout_type = self._classify_workout(raw)

        return Workout(
            date=workout_date,
            workout_type=workout_type,
            description=raw.get("description", ""),
            source="concept2_api",
            total_distance_m=raw.get("distance"),
            total_time_seconds=raw.get("time", 0) / 10.0 if raw.get("time") else None,  # C2 gives tenths
            avg_split_seconds=self._calc_split(raw),
            avg_watts=raw.get("avg_watts"),
            avg_spm=raw.get("stroke_rate"),
            avg_drive_length_m=raw.get("drive_length"),
            drag_factor=raw.get("drag_factor"),
            avg_hr=raw.get("heart_rate", {}).get("average") if isinstance(raw.get("heart_rate"), dict) else None,
            max_hr=raw.get("heart_rate", {}).get("max") if isinstance(raw.get("heart_rate"), dict) else None,
            concept2_id=str(raw.get("id", "")),
        )

    def parse_intervals(self, raw: dict, workout_id: int) -> list[WorkoutInterval]:
        """Parse interval/split data from a Concept2 result."""
        intervals = []
        for i, split in enumerate(raw.get("splits", []), 1):
            intervals.append(WorkoutInterval(
                workout_id=workout_id,
                interval_number=i,
                distance_m=split.get("distance"),
                time_seconds=split.get("time", 0) / 10.0 if split.get("time") else None,
                split_seconds=self._calc_split(split),
                watts=split.get("watts"),
                spm=split.get("stroke_rate"),
                avg_hr=split.get("heart_rate", {}).get("average") if isinstance(split.get("heart_rate"), dict) else None,
                max_hr=split.get("heart_rate", {}).get("max") if isinstance(split.get("heart_rate"), dict) else None,
                rest_seconds=split.get("rest_time", 0) / 10.0 if split.get("rest_time") else None,
            ))
        return intervals

    def _classify_workout(self, raw: dict) -> str:
        """Classify a C2 workout into training categories."""
        distance = raw.get("distance", 0)
        time_tenths = raw.get("time", 0)
        workout_type = raw.get("workout_type", "")

        if workout_type == "FixedDistanceInterval" or workout_type == "FixedTimeInterval":
            return "interval"
        if distance and distance <= 500:
            return "test"
        if distance and distance == 2000:
            return "test"
        if distance and distance == 6000:
            return "test"
        if time_tenths and time_tenths >= 30 * 60 * 10:  # 30+ minutes
            return "steady_state"
        return "general"

    @staticmethod
    def _calc_split(data: dict) -> float | None:
        """Calculate 500m split from distance and time."""
        distance = data.get("distance")
        time_tenths = data.get("time")
        if distance and time_tenths and distance > 0:
            time_seconds = time_tenths / 10.0
            return (time_seconds / distance) * 500
        return None

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
