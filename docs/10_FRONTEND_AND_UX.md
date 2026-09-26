# 10 — Frontend & Farmer UX

## Design Principles

- Mobile-first Progressive Web App (PWA)
- Regional language support (Marathi + English for pilot)
- Voice input/output where feasible
- Visual rather than technical recommendations
- Low-bandwidth friendly
- Always show confidence + evidence

---

## Suggested Stack

- Next.js 14+ (App Router) + React
- Tailwind CSS
- Recharts for numeric charts
- SVG / Lottie for crop growth visualizer
- Workbox or Next.js PWA plugin

---

## Key Screens (Farmer)

### 1. Onboarding
- Create farmer + field
- Select region (Kolhapur / Jalgaon)
- Select crop + sowing date

### 2. Soil Report Upload
- Camera / file picker
- OCR preview with confidence per field
- Farmer confirms or corrects values
- Only confirmed values update the twin

### 3. Dashboard (main)

```
┌─────────────────────────────────────────────┐
│ AgroTwin                       Field A-104  │
├─────────────────────────────────────────────┤
│ CROP: Rice • Tillering Stage                │
│                                             │
│ SOIL HEALTH: 72 / 100                       │
│ N   █████░░░░                               │
│ P   ███████░░                               │
│ K   ██████░░░                               │
├─────────────────────────────────────────────┤
│ CURRENT PLAN                                │
│ Next action        [...]                    │
│ Quantity           [...]                    │
│ Application window [...]                    │
│ Estimated cost     ₹[...]                   │
│ Confidence         HIGH                     │
│ [ WHY THIS PLAN? ]   [ SIMULATE ]           │
├─────────────────────────────────────────────┤
│ ⚠ ACTIVE ALERT                             │
│ Rainfall forecast changed.                  │
│ Current plan is being reviewed.             │
│ [VIEW ANALYSIS]                             │
└─────────────────────────────────────────────┘
```

### 4. Why This Plan
- Expands the six questions
- Shows evidence citations with source + page

### 5. What-If Simulator
- Slider / buttons for −20 % fertilizer, rainfall change, etc.
- Shows delta plan + new confidence

### 6. Visual Growth Simulator
- Side-by-side plant states for Current vs What-If plan
- Scrubber or auto-play

### 7. Alerts / History

---

## Agronomist Dashboard (separate route)

- Active farms count, alerts, low-confidence recs
- Flagged recommendations table
- System health (RAG, weather API, model version)
- Override / feedback form

---

## Implementation Notes

- All numbers come from the API; frontend never calculates fertilizer.
- Low-confidence and ABSTAIN states must be visually distinct and actionable.
- Voice example: “मी उद्या खत टाकू का?” → answered from current twin + weather + evidence, not generic LLM knowledge.

---

## Checklist

- [ ] PWA manifest + offline shell
- [ ] Dashboard matches the wireframe above
- [ ] Proof-carrying recommendation expandable
- [ ] What-If calls `/what-if` and shows delta
- [ ] Growth visualizer uses fixed SVG states mapped to model bands
- [ ] Agronomist view protected by simple role check
