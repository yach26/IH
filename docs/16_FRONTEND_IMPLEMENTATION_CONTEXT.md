You are working on the frontend of AgroTwin AI.

IMPORTANT:
The existing docs/ directory is the source of truth for the project architecture, features,
USPs, backend contracts, agents, ML, RAG, OCR, weather integration, recommendation engine,
digital twin and safety constraints.

DO NOT invent product functionality that is not supported by the project documentation.

Read and use these documents before making architectural decisions:

- docs/00_CONTEXT.md
- docs/01_PROJECT_OVERVIEW.md
- docs/02_DIGITAL_TWIN_AND_LEDGER.md
- docs/03_DATABASE_SCHEMA.md
- docs/04_MULTI_AGENT_ARCHITECTURE.md
- docs/05_RECOMMENDATIONS_PIPELINE.md
- docs/06_AGENTIC_RAG.md
- docs/07_OPTIMIZATION_AND_RULES.md
- docs/08_MONITORING_AND_EVENT_...
- docs/09_API_BACKEND.md
- docs/10_FRONTEND_AND_UX.md
- docs/11_OCR_PIPELINE.md
- docs/12_WEATHER_INTEGRATION.md
- docs/13_WHAT_IF_AND_VISUALIZER.md
- docs/14_SAFETY_CONFIDENCE_...
- docs/15_DEPLOYMENT_...
- docs/IMPLEMENTATION_ORDER.md

The frontend must represent the actual AgroTwin architecture rather than becoming a generic
"AI farming dashboard".

CORE PRODUCT:

AgroTwin is a living, evidence-grounded farm digital twin for continuous nutrient monitoring
and sustainable fertilizer optimization.

The three primary USPs are:

1. Living Farm Digital Twin + Nutrient Ledger
2. Agentic Continuous Monitoring + Event-Driven Replanning
3. Evidence-Grounded Multi-Objective Fertilizer Optimization

The frontend should make these concepts visible without overwhelming the user.

DESIGN DIRECTION:

Create a premium, modern agricultural SaaS interface.

Visual characteristics:
- light theme
- warm off-white / very light beige page background
- white surfaces/cards
- deep slate text
- restrained agricultural green / teal as the primary accent
- subtle terracotta/orange for warnings
- muted neutral borders
- generous whitespace
- strong typography hierarchy
- subtle shadows only
- medium-small border radii
- clean grid system
- professional SaaS/product aesthetic

DO NOT create:
- cyberpunk UI
- neon green
- dark dashboard
- excessive glassmorphism
- glowing borders
- excessive gradients
- huge rounded cards everywhere
- excessive floating elements
- excessive badges
- decorative AI brain graphics
- random circuit patterns
- unnecessary 3D objects
- "AI slop" visuals
- giant hero typography that wastes space
- sidebars unless explicitly required
- dense dashboard walls of tiny cards

NAVIGATION:

Use a clean TOP NAVIGATION rather than a permanent left sidebar.

Suggested structure:

AgroTwin AI logo
Overview
Farm
Simulator
Insights
Command Center

right side:
region/field selector
notifications
user profile

The top navigation should remain consistent across authenticated pages.

The UI must feel like one coherent product rather than five independently designed websites.

RESPONSIVE:

Desktop-first because this is a hackathon demo, but make layouts responsive.

Use:
- CSS grid
- flexbox
- sensible max-width
- responsive breakpoints
- no fixed-position layouts that break at different resolutions

TECHNICAL:

Use the project's existing frontend stack.

Prefer reusable components:
- Button
- Card
- Badge
- Metric
- SectionHeader
- Tabs
- Select
- Slider
- ProgressIndicator
- Alert
- DataTable
- Chart
- EmptyState
- Tooltip
- Modal/Drawer
- TopNavigation

Do not duplicate components between pages.

DATA:

Until backend APIs are connected, create a clearly separated mock-data layer.

Do NOT hardcode fake API responses throughout JSX.

Create a structure such as:

src/
  components/
  pages/
  layouts/
  data/
    mock/
  services/
  hooks/
  types/
  lib/

Mock data must follow the actual backend/domain terminology from docs.

IMPORTANT:

Do not fabricate agronomic numbers.

If mock values are necessary for UI development, clearly isolate them as demo data
and make it easy to replace them with API responses.

Do not make claims such as:
"fertilizer reduction increases yield by 12%"
unless that number actually comes from the backend/model.

The frontend should display model outputs, not invent model outputs.

3D:

The What-If page will eventually use crop-specific 3D models.

Pilot crops:
- Jalgaon: Banana, Cotton
- Kolhapur: Sugarcane, Rice

The visualizer should therefore be architected around a generic CropModel interface
rather than hardcoding the UI for rice.

The frontend should support:
banana
cotton
sugarcane
rice

Growth visuals must be driven by model signals such as:
- growth stage
- vigor
- nutrient sufficiency
- water stress
- projected outcome band

The visualizer is a rendering layer, NOT a prediction engine.

QUALITY BAR:

Every page should look like a real product that could be shown to judges.

Prioritize:
clarity > decoration
hierarchy > density
consistency > novelty
real product behavior > visual gimmicks

Before implementing anything:
1. inspect the repository
2. inspect the docs
3. inspect existing frontend code
4. reuse existing components where possible
5. identify conflicts before changing architecture

Do not overwrite existing backend/ML/agent work.
Frontend work must remain modular and independently testable.