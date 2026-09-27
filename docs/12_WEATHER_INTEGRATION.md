# 12 — Weather Integration

## Requirements

- Reliable weather API (OpenWeatherMap, WeatherAPI, or India-specific source)
- Current conditions + 3–7 day forecast
- Ability to detect significant changes (especially heavy rain probability)
- Application window suitability check

---

## Weather Agent Responsibilities

- Fetch and cache forecast for the field location
- Assess whether the current recommendation’s application window is still valid
- Emit `WEATHER_FORECAST_CHANGED` or `HEAVY_RAIN_ALERT` when thresholds are crossed
- Provide risk flags to the Validation Agent and Growth Visualizer

---

## Threshold Example (configurable)

```yaml
heavy_rain_alert:
  rain_mm_next_48h: 20
  probability: 0.6
```

---

## Demo Strategy

For the hackathon demo, provide a simple admin / script endpoint that injects a synthetic heavy-rain forecast.  
This guarantees the “wow” moment works even if the live API is unavailable or rate-limited.

```
POST /events
{
  "type": "HEAVY_RAIN_ALERT",
  "field_id": "...",
  "payload": {
    "rain_mm_next_48h": 45,
    "probability": 0.85,
    "source": "demo_injection"
  }
}
```

---

## Checklist

- [x] Weather client with caching (in-memory)
- [x] Weather Agent that can emit events
- [x] Threshold configuration loaded from region config
- [x] Demo injection endpoint
- [x] Integration with Monitoring Agent

### Verified live (Phase 4.2, 2026-09-27)

- Real, unmocked fetch to the live Open-Meteo API confirmed working from this
  environment (`test_real_network_happy_path`) — a 200 response with a real
  7-day precipitation forecast for a Kolhapur field.
- Fixed a real bug: `get_weather_context`'s in-memory cache
  (`CACHE_TTL_SECONDS = 900`) was **dead code** — `force_refresh` defaulted to
  `True` and `app/pipeline.py` never overrode it, so every `/recommend` call
  re-fetched from the network regardless of the cache. Fixed in
  `app/agents/weather_agent.py` (the `elif force_refresh:` branch was merged
  into an unconditional "fetch if still no snapshot" step, so a cache miss with
  `force_refresh=False` now actually fetches instead of silently returning no
  data) and `app/pipeline.py` (now passes `force_refresh=False`). Verified a
  repeat call within the TTL window makes zero additional network calls and
  returns the same `snapshot_id` (`test_real_fetch_is_cached_on_repeat_call`).
- Threshold-crossing logic (`rainfall_probability_pct=70`,
  `rainfall_mm_next_7d=50`, `region_config.py`) verified against a
  real-shaped forecast payload, not just the demo injection path
  (`test_real_forecast_crosses_heavy_rain_threshold`).
