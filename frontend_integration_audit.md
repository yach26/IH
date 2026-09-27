# Frontend Data Audit & Integration Changelog

*Last updated: 2026-09-27 | All REAL-001 (Polgaon, Kolhapur) data*

---

## 1. Landing Page (`/`)

### ✅ Dynamic (Live from Backend)
* **HeroSection Overlays:** The floating field card ("Field REAL-001 · Sugarcane · Grand Growth") and the soil health score ("45/100") now fetch from `GET /fields/REAL-001/twin` on mount. Weather shows real 7-day rainfall forecast from open-meteo via the weather agent.
* **Pilot Regions Map:** Dynamically fetches all fields from `GET /fields` and plots each as a pulsing gold pin on the map (8 real Kolhapur fields shown).

### ⚠️ Still Static (by design — marketing copy)
* **Capability Strip / Impact Numbers:** "24% Yield Increase" etc. are editorial marketing content — not meant to be real-time.

---

## 2. Dashboard (`/dashboard`)

### ✅ Dynamic (Live from Backend / RAG / ML / DB)
All data flows from `GET /fields/REAL-001/twin` which is enriched server-side:

| Section | Source |
|---|---|
| **Field ID, Crop, Stage** | `field_active_crop` view JOIN `crops` table → `crop_name = "Sugarcane"` |
| **Area & Location** | `fields` table `(lat=16.0644, lon=74.1352, area_ha=2)` |
| **Field Map** | Leaflet map centred on real lat/lon from DB |
| **Soil N/P/K** | Real Polgaon SHC data (N: 258.7, P: 2.33, K: 69.26 kg/ha) |
| **Soil pH & OC%** | Real SHC (pH: 6.26, OC: 1.096%) |
| **Soil Health Score** | Derived from N/P/K vs sugarcane crop requirements (score: 45/100) |
| **Nutrient progress bars** | Scored against real crop targets (N: 340, P: 30, K: 170 kg/ha) |
| **Crop condition** | Derived: N-sufficiency score ≥60% → "Good", else "Moderate" |
| **Water stress** | Derived: `heavy_rain_alert` flag from open-meteo weather agent |
| **Overall Field Status** | Composite of above |
| **Rain forecast (7d)** | `17 mm` from open-meteo via weather agent |
| **Recommendation Action** | RAG + heuristic optimizer: `"DAP + Urea + MOP"` |
| **Fertilizer Quantities** | Real: `DAP 358 + Urea 36.7 + MOP 167.8 kg/ha` |
| **Application Window** | `"2026-09-28 – 2026-09-30"` (dry window from weather agent) |
| **Estimated Cost** | ₹13,242 (heuristic from optimizer) |
| **Confidence Level** | `"MEDIUM"` from agent pipeline |
| **RAG Citation** | `"06_Fertilizer_Recommendations/mpkv_icar_rdf.md"` |
| **Crop Stage Timeline** | Built from `stageSequence` from DB for the specific crop |
| **Active Alert** | Dynamically prepended from monitoring agent alerts |

### ⚠️ Still Static (no source available yet)
* **Daily weather bar chart days** — Mon-Sun bar chart height values (partial; total 7d rainfall is real).
* **Pest risk / Disease risk** — "Moderate / Low" static because pest agent not yet implemented.

---

## 3. Simulator (`/simulator`)

### ✅ Dynamic (Live from Backend / ML Models)
* **Crop auto-selection:** Page loads with the real active crop (`Sugarcane`) auto-selected.
* **Baseline N slider init:** Pre-set to the real `soilGap.N = 81 kg/ha` from the RAG ledger (the actual N deficit to fill) instead of a hardcoded crop default.
* **What-If prediction:** Every slider move triggers `POST /fields/REAL-001/what-if` → real XGBoost Kolhapur model → live `yieldBand`, `confidence`, `cost` displayed.
* **Explanation text:** Shows AI yield projection with real numbers (e.g., `"76.0-84.0 t/ha"`).
* **Citation banner:** Displays `"MPKV-ICAR RDF Kolhapur 2022"` in the header.
* **Live field badge:** Shows `"Live · Sugarcane · Grand Growth"` in the header.
* **Growth Stage Timeline:** Built from `stageSequence` from DB, not hardcoded.

### ⚠️ Still Static (no source available yet)
* **Historical Yield Trend Chart:** Multi-year historical chart not yet wired (no historical yield table in DB).

---

## Technical Changes Summary

### Backend (`agrotwin_api/app/api/routes.py`)
1. **Fixed `_field_row`:** Added `LEFT JOIN crops c ON c.crop_id = fac.current_crop_id` — now `crop_name = "Sugarcane"` is always available.
2. **Fixed `list_fields`:** `fac.crop_code` → `c.crop_name` to match actual schema.
3. **Enriched `/fields/{id}/twin` response** with:
   - `soilHealthScore` (derived from N/P/K vs crop targets)
   - `soilDetail` (ph, oc_percent, n_score, p_score, k_score)
   - `stageSequence` (crop-specific ordered list of stages)
   - `growthStageRaw` (canonical key like `GRAND_GROWTH`)
   - `currentPlan.fertilizerBreakdown` (DAP/Urea/MOP kg/ha)
   - `currentPlan.citation` (RAG source document)
   - `currentPlan.soilGap` (N/P2O5/K2O gaps)
   - `weather` block (open-meteo rainfall, heavy_rain_alert)
   - `lat`, `lon` as separate numeric fields

### Frontend (`agrotwin_frontend/src/`)
1. **`app/dashboard/page.tsx`** — Full rewrite: all hardcoded defaults replaced with live API data; field status derived from real N-sufficiency and weather agent; timeline built from `stageSequence`; fertilizer plan shows real DAP+Urea+MOP quantities + cost + confidence + citation.
2. **`components/landing/HeroSection.tsx`** — Now fetches twin data on mount; shows real field ID, crop, stage, soil health score, and rainfall forecast.
3. **`components/ui/PilotRegionsMap.tsx`** — Fetches all `GET /fields` and plots all 8 real Kolhapur fields.
4. **`app/simulator/page.tsx`** — Fetches twin data on mount; auto-selects crop; pre-sets N slider to real soil gap; shows citation and live field badge in header.
