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

- [ ] Weather client with caching (Redis or in-memory)
- [ ] Weather Agent that can emit events
- [x] Threshold configuration loaded from region config
- [x] Demo injection endpoint
- [x] Integration with Monitoring Agent
