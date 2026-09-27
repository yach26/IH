# Architecture Decision Record: AgroTwin AI

## ADR-001: Fertilizer Quantities Stay Deterministic

### Status
Accepted

### Context
The system needs to recommend fertilizer quantities (kg/ha of Urea, DAP, MOP) for farmers. We considered using an LLM to generate these quantities based on soil tests, crop type, and growth stage.

### Decision
**All fertilizer quantities come exclusively from the deterministic Nutrient Ledger + Optimizer.** The LLM is used only for narrative explanations (e.g., "Why this plan?"), never for quantities.

### Consequences

**Positive:**
- Quantities are reproducible, auditable, and explainable
- No risk of LLM hallucinating dangerous quantities
- System works fully offline without API keys
- Every quantity can be traced back to a published RDF source

**Negative:**
- Less flexible than a learned model (cannot adapt to micro-variability)
- Requires manual updates when new fertilizer products are introduced

### Alternatives Considered
1. **LLM-generated quantities** — Rejected: too risky for agricultural safety
2. **Pure ML regression** — Rejected: no real training data available; would be synthetic
3. **Hybrid (LLM suggests, Ledger disposes)** — Rejected: still allows LLM to influence quantities

---

## ADR-002: Yield Model is Read-Only

### Status
Accepted

### Context
We have an XGBoost yield model that predicts crop yield given a fertilizer plan. We considered allowing the model to suggest plan adjustments.

### Decision
**The yield model is strictly read-only.** It receives a plan from the Ledger and predicts yield. It never modifies, suggests, or influences the plan.

### Consequences

**Positive:**
- Clear separation of concerns: Ledger decides, model predicts
- No risk of model overriding published RDF values
- Model can be retrained without affecting the recommendation engine

**Negative:**
- Cannot optimize for yield directly (would need a different architecture)
- Model predictions are not actionable for plan adjustment

---

## ADR-003: OCR Requires Farmer Confirmation

### Status
Accepted

### Context
We use EasyOCR to extract soil nutrient values from Soil Health Card images. OCR is imperfect and can misread values.

### Decision
**No OCR value is written to the Digital Twin without explicit farmer confirmation.** The upload-preview-confirm flow is mandatory.

### Consequences

**Positive:**
- Prevents incorrect data from corrupting the Digital Twin
- Farmer is always in control of their data
- LLM-refined values (confidence 0.80) can never be auto-accepted

**Negative:**
- Adds a step to the workflow (farmer must review and confirm)
- Slower than fully automated extraction

---

## ADR-004: Dual Database Support (SQLite + Postgres)

### Status
Accepted

### Context
The system needs to run locally (demo, development) and in production (cloud).

### Decision
**`DATABASE_URL` is the single switch.** Empty = SQLite (local/demo), set = Postgres (production).

### Consequences

**Positive:**
- Zero-config local development
- Easy production deployment
- No code changes needed between environments

**Negative:**
- Schema drift between SQLite and Postgres (mitigated by `PostgresCursorWrapper`)
- Some SQL features differ between the two

---

## ADR-005: Event-Driven Monitoring

### Status
Accepted

### Context
The system needs to respond to external events (heavy rain, soil report updates, crop stage changes).

### Decision
**An in-process EventBus with typed events.** The MonitoringAgent subscribes to events and triggers selective re-planning.

### Consequences

**Positive:**
- Loose coupling between event producers and consumers
- Selective re-planning (only affected agents re-run)
- Audit trail via `audit_log` table

**Negative:**
- In-process only (not distributed)
- Single point of failure (the MonitoringAgent)
