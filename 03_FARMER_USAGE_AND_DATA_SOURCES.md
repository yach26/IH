# External Data Sources & The Farmer's Experience

## Part A — Where every number in the app actually comes from

AgroTwin never invents an agronomic value. Here is exactly what backs each
piece of data shown anywhere in the product.

| What you see | Real source | File it lives in |
|---|---|---|
| Fertilizer dose targets (N/P₂O₅/K₂O per crop+stage) | MPKV (Mahatma Phule Krishi Vidyapeeth) & ICAR Recommended Dose of Fertilizer guidelines | `rag/docs/mpkv_icar_rdf.md`, `jalgaon_rdf.md` → seeded into `fertilizer_recommendations` table |
| Fertilizer product composition (DAP/Urea/MOP % N-P-K) | Fertilizer Control Order (FCO) specification | `rag/docs/fco_fertilizer_spec.md` → `fertilizer_products` table |
| Crop growth-stage timing | ICAR-NRRI + MPKV Rahuri Extension Bulletins, 2022 | `rag/docs/crop_calendars.md` → `crop_calendars` table |
| Elemental-to-oxide nutrient conversion (P×2.2919, K×1.2046) | FAO, "Crop production levels and fertilizer use", Appendix Table 16 | `app/core/nutrients.py` |
| Weather forecast (7-day rainfall, heavy-rain risk) | Open-Meteo public forecast API, live, per field's own GPS coordinates | `app/agents/weather_agent.py` |
| Soil test values | The farmer's own uploaded soil health card (OCR-read) or lab report — never a generic default | `app/core/ocr.py`, `soil_tests` table |
| Real regional soil statistics (used to ground evidence) | Real Kolhapur district Soil Health Card dashboards, 2016–2024 Polgaon soil records | `data/real_kolhapur/`, `app/core/kolhapur_context.py` |
| Yield estimate | XGBoost models trained on real Polgaon soil records + published Kolhapur yield averages | `ml/model_card.md`, `app/yield_prediction.py` — explicitly a directional estimate, abstains outside its trained scope |
| Cost estimate | An engineering-default placeholder — **not** a sourced fertilizer price table (explicitly labelled "not a sourced price" everywhere it's shown) | — |
| Districts/geography | Real Maharashtra district names (Kolhapur & Jalgaon have sourced lat/lon boundaries; the other 34 districts are added as real administrative names without invented boundary data) | `seed_data.py` |

**What this means in practice**: if the system doesn't have a real number
for something, it says so — "Not available", "Weather unavailable",
"No recommendation generated yet" — rather than showing a plausible-looking
fake value. This is the single most important safety property of the
product for a real farmer: a wrong "confident-looking" number is far more
dangerous than an honest "we don't know yet."

---

## Part B — What happens when a real farmer uses this

### Step 1 — Registering a field
The farmer (or an extension worker on their behalf) opens the app, selects
their real district (any Maharashtra district, or "Other" if outside
Maharashtra — not forced into a false Kolhapur/Jalgaon label), enters field
area, irrigation type, and — if they know it — their field's GPS
coordinates. The more accurate the coordinates, the more accurate the
weather forecast will be, but the app works even without them (weather
just shows "not available" honestly).

### Step 2 — Telling the system what's planted
The farmer selects their crop (Sugarcane, Banana, Cotton, or Soybean today)
and the date it was sown. From that point on, the app tracks **which growth
stage the crop is actually in right now**, computed from real elapsed days
against a sourced agricultural calendar — it advances on its own; the
farmer doesn't have to keep updating it.

### Step 3 — Uploading a soil health card
The farmer photographs or scans their government/lab Soil Health Card and
uploads it. The system reads the nutrient values (Nitrogen, Phosphorus,
Potassium, pH, Organic Carbon, Electrical Conductivity) automatically, and
shows the farmer **exactly what it read, with a confidence score per
value**. Any value the system isn't confident about is flagged for the
farmer to double-check or correct by hand. **Nothing is saved to the
field's real record until the farmer confirms it** — a wrong OCR reading
can never silently become the basis for a fertilizer recommendation.

### Step 4 — Getting the recommendation
Once soil data is confirmed, the farmer opens their Farm dashboard. Front
and centre is the **Official Recommendation**: large, unmissable numbers
for exactly how much of each fertilizer product to apply, a plain-language
explanation of why (based on their real soil numbers and their crop's
current stage), a numbered list of next steps (when to apply, and what to
do if anything is unresolved), and a confidence stamp (HIGH/MEDIUM/LOW).
If the system isn't confident enough to safely recommend a plan, it says
so plainly and explains exactly what's missing — it does not guess.

The farmer can tap **"Listen"** to have the whole thing read aloud in
English, Hindi, or Marathi — useful for anyone who finds reading a long
technical screen difficult.

### Step 5 — Seeing the bigger picture
The dashboard also shows: current soil nutrient levels with a plain
High/Moderate/Low read, this week's weather forecast and whether it's
suitable for applying fertilizer right now (heavy rain before application
wastes fertilizer and pollutes runoff — the system will actively tell the
farmer to wait), the field's location on a map, and a timeline showing
which growth stage the crop is in.

### Step 6 — Testing "what if"
Before committing to a plan, the farmer (or an advisor) can open the
**What-If Simulator** and try adjusting fertilizer amount, expected
rainfall, irrigation level, and timing, to see how the crop's condition and
the fertilizer plan would change — without touching the real, official
recommendation. This is clearly labelled as a scenario tool, not a second
opinion from the AI.

### Step 7 — Staying up to date automatically
If a heavy-rain event is forecast, if the farmer logs that they actually
applied fertilizer, or if a new soil test comes in, the system
**automatically re-evaluates the plan** — the farmer doesn't have to
remember to ask again. A notification/alert appears on their dashboard
(and on the fleet-wide Insights page, for an agronomist overseeing many
farmers) explaining exactly what changed and why the plan was updated.

### Step 8 — Human oversight, always available
An agronomist or extension officer can review the full history of every
recommendation ever generated for a field — what changed, when, and why —
and can override any specific recommendation with a documented reason
(e.g. "farmer reports visible potassium deficiency in the field, not
captured by the lab soil test"). This override is fully audited and
immediately reflected back to the farmer's dashboard.

### What the farmer never has to worry about
- Being shown a fake or default number when the system doesn't actually
  know something.
- A wrong OCR reading silently entering their field's record.
- The system inventing a yield or cost promise it can't actually back up.
- Losing their selected field when navigating between screens.
- Being locked out of the system just because their district isn't one of
  the two original pilot districts.
