"""
Weather Agent — integrates Open-Meteo forecast API (Phase-2).

Responsibility:
  - Fetch 7-day weather forecast (precipitation metrics) based on field lat/lon.
  - Store snapshot in weather_snapshots table.
  - Parse rainfall probability and next 7-day cumulative rainfall.
  - Raise HEAVY_RAIN_ALERT if thresholds are exceeded.

Source reference:
  04_Weather/weather_sources.md specifies Open-Meteo for hackathon prototype.
  Open-Meteo requires latitude and longitude.

Threshold (ENGINEERING_DEFAULT):
  heavy_rain_alert = rainfall_probability >= 70% AND rainfall_mm_next_7d >= 50 mm.
  (This is a placeholder agronomic rule — see Gap #6. Soluble N fertilizers
   leach under heavy rain; 50mm is a safe conservative trigger for alerting.)
"""

import sqlite3
import json
from datetime import datetime, timezone
import requests


# Open-Meteo API URL for daily precipitation forecast
API_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_context(
    conn: sqlite3.Connection,
    field_id: int,
    lat: float | None,
    lon: float | None,
    force_refresh: bool = True,
    mock_snapshot: dict | None = None,
) -> dict:
    """
    Returns a dict with weather alerts and parsed metrics.
    If mock_snapshot is provided, it skips the network call (used for testing).
    """
    flags: list[str] = []

    if lat is None or lon is None:
        flags.append("NO_COORDINATES (Cannot fetch weather without field lat/lon)")
        return {
            "heavy_rain_alert": False,
            "flags": flags,
            "snapshot": None,
            "warning": "NO_COORDINATES",
        }

    # Fetch fresh snapshot
    snapshot = None
    if mock_snapshot:
        snapshot = _insert_snapshot_from_mock(conn, field_id, mock_snapshot)
    elif force_refresh:
        try:
            snapshot = _fetch_and_store_snapshot(conn, field_id, lat, lon)
        except Exception as e:
            flags.append(f"WEATHER_FETCH_ERROR ({e})")
            # Fall back to latest stored snapshot if available
            snapshot = _get_latest_snapshot(conn, field_id)

    if snapshot is None:
        return {
            "heavy_rain_alert": False,
            "flags": flags,
            "snapshot": None,
        }

    alert_active = bool(snapshot["heavy_rain_alert"])
    alert_details = ""
    if alert_active:
        alert_details = (
            f"7-day rainfall forecast: {snapshot['rainfall_mm_next_7d']} mm "
            f"(threshold: 50 mm); max precipitation probability: "
            f"{snapshot['rainfall_probability']}% (threshold: 70%). "
            "ENGINEERING_DEFAULT thresholds — see weather_agent.py docstring."
        )

    return {
        "heavy_rain_alert": alert_active,
        "alert_details": alert_details,
        "flags": flags,
        "snapshot": snapshot,
    }


def _fetch_and_store_snapshot(
    conn: sqlite3.Connection, field_id: int, lat: float, lon: float
) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 7,
    }
    resp = requests.get(API_URL, params=params, timeout=5.0)
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily", {})
    p_sum = daily.get("precipitation_sum", [])
    p_prob = daily.get("precipitation_probability_max", [])

    mm_7d = round(sum(val for val in p_sum if val is not None), 1)
    max_prob = max((val for val in p_prob if val is not None), default=0)

    alert = (max_prob >= 70 and mm_7d >= 50.0)

    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO weather_snapshots
           (field_id, fetched_at, forecast_json, rainfall_probability,
            rainfall_mm_next_7d, heavy_rain_alert, source)
           VALUES (?,?,?,?,?,?,?)""",
        (field_id, now_iso, json.dumps(data), max_prob, mm_7d, int(alert), 'open-meteo'),
    )
    conn.commit()
    new_id = cur.lastrowid
    return _get_snapshot_by_id(conn, new_id)


def _insert_snapshot_from_mock(conn: sqlite3.Connection, field_id: int, mock: dict) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO weather_snapshots
           (field_id, fetched_at, forecast_json, rainfall_probability,
            rainfall_mm_next_7d, heavy_rain_alert, source)
           VALUES (?,?,?,?,?,?,?)""",
        (field_id, now_iso, json.dumps(mock.get("raw_json", {})),
         mock.get("rainfall_probability", 0), mock.get("rainfall_mm_next_7d", 0),
         int(mock.get("heavy_rain_alert", False)), mock.get("source", "mock")),
    )
    conn.commit()
    return _get_snapshot_by_id(conn, cur.lastrowid)


def _get_latest_snapshot(conn: sqlite3.Connection, field_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM weather_snapshots WHERE field_id = ? ORDER BY fetched_at DESC LIMIT 1",
        (field_id,),
    ).fetchone()
    return dict(row) if row else None


def _get_snapshot_by_id(conn: sqlite3.Connection, snap_id: int) -> dict:
    row = conn.execute("SELECT * FROM weather_snapshots WHERE snapshot_id = ?", (snap_id,)).fetchone()
    return dict(row)
