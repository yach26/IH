"""
Weather Agent — integrates Open-Meteo forecast API (Phase-2).

Responsibility:
  - Fetch 7-day weather forecast (precipitation metrics) based on field lat/lon.
  - Cache snapshots in-memory (TTL) and in weather_snapshots.
  - Raise HEAVY_RAIN_ALERT if region-config thresholds are exceeded.
  - Optionally emit WEATHER_FORECAST_CHANGED / HEAVY_RAIN_ALERT via refresh_and_emit.

Source reference:
  04_Weather/weather_sources.md specifies Open-Meteo for hackathon prototype.

Thresholds live in region_config (ENGINEERING_DEFAULT pending Gap #6).
"""

import sqlite3
import json
import time
from datetime import datetime, timezone
import requests

from ..core.region_config import load_region_config

# Open-Meteo API URL for daily precipitation forecast
API_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL_SECONDS = 900  # 15-minute in-memory cache (doc 12)
_CACHE: dict[tuple[float, float], tuple[float, dict]] = {}


def weather_thresholds() -> tuple[float, float]:
    w = load_region_config()["rules"]["weather_windows"]
    return float(w["rainfall_probability_pct"]), float(w["rainfall_mm_next_7d"])


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

    # Fetch fresh snapshot (in-memory cache for live API calls)
    snapshot = None
    cache_key = (round(float(lat), 4), round(float(lon), 4))
    if mock_snapshot:
        snapshot = _insert_snapshot_from_mock(conn, field_id, mock_snapshot)
    elif not force_refresh and cache_key in _CACHE:
        ts, cached = _CACHE[cache_key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            snapshot = cached
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
        prob_th, mm_th = weather_thresholds()
        alert_details = (
            f"7-day rainfall forecast: {snapshot['rainfall_mm_next_7d']} mm "
            f"(threshold: {mm_th} mm); max precipitation probability: "
            f"{snapshot['rainfall_probability']}% (threshold: {prob_th}%). "
            "ENGINEERING_DEFAULT thresholds — see region_config.py."
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

    prob_th, mm_th = weather_thresholds()
    alert = (max_prob >= prob_th and mm_7d >= mm_th)

    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO weather_snapshots
           (field_id, fetched_at, forecast_json, rainfall_probability,
            rainfall_mm_next_7d, heavy_rain_alert, source)
           VALUES (?,?,?,?,?,?,?)""",
        (field_id, now_iso, json.dumps(data), max_prob, mm_7d, bool(alert), 'open-meteo'),
    )
    conn.commit()
    new_id = cur.lastrowid
    snap = _get_snapshot_by_id(conn, new_id)
    _CACHE[(round(float(lat), 4), round(float(lon), 4))] = (time.time(), snap)
    return snap


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
         bool(mock.get("heavy_rain_alert", False)), mock.get("source", "mock")),
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
