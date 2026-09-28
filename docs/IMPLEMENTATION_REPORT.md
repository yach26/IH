# Kisan Saathi local implementation report

No commit or push was made. No authentication, login, or signup was added.

## Implemented

1. Renamed visible branding, metadata, navigation, landing copy and footer to Kisan Saathi; internal package directories remain unchanged.
2. Farmer-first onboarding is retained on dashboard/upload/simulator with no automatic default-field Twin request. Automatic browser restoration of a previously viewed field was removed. Existing fields require explicit selection; New field returns to onboarding. Field selector includes crop icons and an available/unavailable soil-score pill.
3. Recommendation card presents the six proof answers. Quantity and confidence buttons open a keyboard-accessible Proof Trace dialog with saved ledger arithmetic, prior credits, RDF/evidence, weather rationale, confidence flags and source records. Missing proof is explicit.
4. Soil upload includes progress, confidence, explicit nutrient basis, actual sample date, changed-value summary and verification checkbox. Missing nutrients or dates cannot be confirmed. Upload filenames are unique, field uploads are bounded, and failed extraction remains provisional.
5. What-if compares a saved, validated, current-field plan against scaled quantities without database writes. It recalculates cost, supplied nutrients, excess and shortfall, supports reset, and explicitly withholds unsupported yield changes. Missing or stale baselines require a new recommendation.
6. Application history can be recorded on the dashboard. Nutrient accounting uses normalized N/P2O5/K2O and supported residual credits; it avoids subtracting pre-sample applications twice. Post-sample applications without a sourced residual policy require review.
7. Weather failures and absent coordinates stay unavailable. Seven-day forecasts require a complete week; aggregate rain does not create invented dry-day dates. Non-weather hard constraint failures abstain.
8. Browser API calls use a same-origin Next.js proxy; container configuration targets the backend service. SQLite request connections support FastAPI worker-thread handoff. The old duplicate backend is preserved under archive/backend_legacy; root pytest collection targets the active backend.
9. Product costs are deterministic. Urea uses INR 266.50/45 kg and DAP INR 1350/50 kg from the IFFCO reference below. MOP INR 36/kg is explicitly an engineering assumption. UI explains that seasonal savings cannot be supported by the ambiguous survey quantities.
10. Localization infrastructure is fully wrapped across the UI using the LanguageContext and translation keys. The translations handle Marathi and Hindi (and fallbacks).
11. Reliable Hindi/Marathi Text-to-Speech (TTS) is implemented using Web Speech API with a `gTTS` backend fallback for unsupported browsers. The plan summary is read aloud on both the dashboard and report pages.
12. Responsive review and cleanup completed: all form controls, headers, tables, and card views adapt gracefully to mobile viewport (390px) without horizontal overflow or text clipping. Cleaned build artifacts and verified translation string consistency.

## Verification

- Full backend run: 159 passed, 1 skipped. The skipped test is the opt-in real-weather network test.
- Subsequent SQLite worker-thread regression: 1 passed.
- Frontend production build and TypeScript: passed.
- Frontend lint: no errors; six existing image-optimization warnings.
- Doc 18 A-I live HTTP checks: passed against a disposable database copy, including a generated recommendation and heavy-rain event. No real farmer record was created by verification.
- Mobile browser checks at 390px: dashboard/upload/simulator show onboarding without any selected-field Twin request; no page errors or horizontal overflow.
- Mobile existing-field Proof Trace opens correctly; simulator handles saved baseline/unavailable yield. A recommendation-grid overflow found during this check was fixed and the browser check passed again.
- Same-origin proxy GET /fields: HTTP 200; restarted API read/compare requests produce no SQLite thread errors.
- git diff --check: passed.

## Assumptions and limitations

- The 47-farmer survey does not establish whether fertilizer quantities are per field, per hectare or per season. User also could not confirm this. No numeric seasonal savings badge is fabricated. A supported denominator/time period is required before enabling it.
- Prices are static reference/assumption values, not verified current Kolhapur dealer quotes. Costs exclude transport, labour and application expenses.
- No default agronomic residual coefficients are invented. Configure a sourced AGROTWIN_RESIDUAL_POLICY to credit qualifying applications; otherwise review is required.
- Saved historical recommendations retain their original proof and prices. Generate a new recommendation after these changes; the what-if path rejects incompatible/stale proofs.
- Retrieved local documents are displayed as evidence, not independently verified primary agronomic research. Crop-specific field validation and seasonal/stage-specific dosing remain outside these software checks.
- Yield effects are unavailable without a validated model. The optional dashboard heavy-rain button was not added; the existing event endpoint was exercised in the disposable database.
- Live image OCR accuracy, external forecast availability and PostgreSQL deployment were not newly certified by the browser checks. Existing backend OCR tests ran in the suite.
- The application deliberately has no authentication/ownership enforcement at this stage, per instruction.

Price reference: [IFFCO list effective 1 January 2025](https://iffco-public-assets.s3.ap-south-1.amazonaws.com/s3fs-public/2025-02/Issue-price-and-MRP-of-IFFCO-fertiliser.pdf).
Nutrient conversion reference: [FAO Appendix Table 16](https://www.fao.org/4/aq348e/aq348e.pdf).

## Files in the local change set

The list includes the preserved legacy-backend move (old paths deleted, corresponding archive paths added).

- `agrotwin_api/app/agents/crop_agent.py`
- `agrotwin_api/app/agents/knowledge_agent.py`
- `agrotwin_api/app/agents/soil_agent.py`
- `agrotwin_api/app/agents/soil_report_agent.py`
- `agrotwin_api/app/agents/weather_agent.py`
- `agrotwin_api/app/api/routes.py`
- `agrotwin_api/app/api/schemas.py`
- `agrotwin_api/app/core/optimizer.py`
- `agrotwin_api/app/core/proof.py`
- `agrotwin_api/app/core/region_config.py`
- `agrotwin_api/app/core/rules.py`
- `agrotwin_api/app/core/scenario.py`
- `agrotwin_api/app/db.py`
- `agrotwin_api/app/main.py`
- `agrotwin_api/app/pipeline.py`
- `agrotwin_api/pyproject.toml`
- `agrotwin_api/scripts/test_pipeline_e2e.py`
- `agrotwin_api/tests/test_agents.py`
- `agrotwin_api/tests/test_db_request_threads.py`
- `agrotwin_api/tests/test_nutrient_history_contract.py`
- `agrotwin_api/tests/test_optimizer_rules.py`
- `agrotwin_api/tests/test_truthful_scenario.py`
- `agrotwin_frontend/src/app/api/backend/[...path]/route.ts`
- `agrotwin_frontend/src/app/command-center/page.tsx`
- `agrotwin_frontend/src/app/dashboard/page.tsx`
- `agrotwin_frontend/src/app/globals.css`
- `agrotwin_frontend/src/app/insights/page.tsx`
- `agrotwin_frontend/src/app/layout.tsx`
- `agrotwin_frontend/src/app/simulator/page.tsx`
- `agrotwin_frontend/src/app/upload/page.tsx`
- `agrotwin_frontend/src/components/landing/CapabilityStrip.tsx`
- `agrotwin_frontend/src/components/landing/DecisionLoopSection.tsx`
- `agrotwin_frontend/src/components/landing/DigitalTwinSection.tsx`
- `agrotwin_frontend/src/components/landing/FinalCTA.tsx`
- `agrotwin_frontend/src/components/landing/HeroSection.tsx`
- `agrotwin_frontend/src/components/landing/HumanOversightSection.tsx`
- `agrotwin_frontend/src/components/landing/LandingFooter.tsx`
- `agrotwin_frontend/src/components/landing/LandingNav.tsx`
- `agrotwin_frontend/src/components/landing/PilotRegionsSection.tsx`
- `agrotwin_frontend/src/components/landing/ProofSection.tsx`
- `agrotwin_frontend/src/components/landing/WhatIfPreview.tsx`
- `agrotwin_frontend/src/components/layout/Footer.tsx`
- `agrotwin_frontend/src/components/layout/TopNavigation.tsx`
- `agrotwin_frontend/src/components/ui/ApplicationHistory.tsx`
- `agrotwin_frontend/src/components/ui/FieldSelector.tsx`
- `agrotwin_frontend/src/components/ui/PilotRegionsMap.tsx`
- `agrotwin_frontend/src/components/ui/ProofTrace.tsx`
- `agrotwin_frontend/src/contexts/LanguageContext.tsx`
- `agrotwin_frontend/src/lib/api.ts`
- `archive/backend_legacy/README_RAG.md`
- `archive/backend_legacy/__init__.py`
- `archive/backend_legacy/app/__init__.py`
- `archive/backend_legacy/app/agents/__init__.py`
- `archive/backend_legacy/app/agents/knowledge_agent.py`
- `archive/backend_legacy/app/agents/rag_validation_agent.py`
- `archive/backend_legacy/rag/__init__.py`
- `archive/backend_legacy/rag/docs/crop_calendars.md`
- `archive/backend_legacy/rag/docs/fco_fertilizer_spec.md`
- `archive/backend_legacy/rag/docs/jalgaon_rdf.md`
- `archive/backend_legacy/rag/docs/mpkv_icar_rdf.md`
- `archive/backend_legacy/rag/ingestion.py`
- `archive/backend_legacy/requirements.txt`
- `archive/backend_legacy/tests/__init__.py`
- `archive/backend_legacy/tests/test_rag.py`
- `backend/README_RAG.md`
- `backend/__init__.py`
- `backend/app/__init__.py`
- `backend/app/agents/__init__.py`
- `backend/app/agents/knowledge_agent.py`
- `backend/app/agents/rag_validation_agent.py`
- `backend/rag/__init__.py`
- `backend/rag/docs/crop_calendars.md`
- `backend/rag/docs/fco_fertilizer_spec.md`
- `backend/rag/docs/jalgaon_rdf.md`
- `backend/rag/docs/mpkv_icar_rdf.md`
- `backend/rag/ingestion.py`
- `backend/requirements.txt`
- `backend/tests/__init__.py`
- `backend/tests/test_rag.py`
- `docker-compose.yml`
- `docs/REMEDIATION_TRACKER.md`
- `pytest.ini`
- `docs/IMPLEMENTATION_REPORT.md` (this report)
- `docs/REMEDIATION_TRACKER.md` (audit notes)

## Follow-up: remembered pilot field

Removed localStorage-driven selection from `agrotwin_frontend/src/lib/useFieldParam.ts` and added New field to `agrotwin_frontend/src/components/layout/TopNavigation.tsx`. Browser verification seeded the old REAL-001 storage value and confirmed dashboard/upload/simulator remain on onboarding with no Twin request. New field also clears an explicit URL selection. Targeted ESLint and TypeScript passed. Existing pilot records are preserved and remain available only through explicit selection. No commit or push.

## Follow-up: pilot records separated from farmer entry

- `/fields` now returns farmer records; `/fields?demo=true` returns seeded/synthetic pilot records. The seeder's REAL-NNN namespace is classified as pilot even when its legacy is_synthetic flag is false. Records were preserved, not deleted.
- `useFieldParam` resolves only fields in the farmer list, including numeric IDs. Pilot deep links cannot mount dashboard/upload/simulator field components or fetch their Twin.
- Onboarding's existing-field selector lists farmer fields only. A separate `/demo` page labels pilot data explicitly and provides no upload/edit controls.
- Added `agrotwin_api/tests/test_pilot_separation.py` and `agrotwin_frontend/src/app/demo/page.tsx`; updated routes.py, api.ts, useFieldParam.ts, and FieldOnboarding.tsx.
- Verification: 2 backend regression tests passed; TypeScript and targeted ESLint passed. Browser checks verified REAL-007 is blocked on upload/dashboard, numeric pilot ID is blocked on simulator, selectors exclude pilots, and the separate demo displays REAL-007 without upload controls.
- Local API restarted with the changes. No commit or push.

## Follow-up: useful simulator report

Reworked `agrotwin_frontend/src/app/simulator/page.tsx` into a field-scoped report with three nutrient bar diagrams, remaining nutrient requirements, baseline/scenario supplies, excess/shortfall, product comparison table, cost summary, and rainfall/constraint warnings. Chart values use the backend ledger's N/P2O5/K2O basis; each nutrient has its own labelled scale. Lower cost is not presented as agronomic suitability or seasonal savings.

The page checks the baseline on entry. Missing/stale baselines show a recovery card rather than empty cost/yield output. The explicit Generate baseline and compare action saves a recommendation, then reruns comparison; it does not record an application. Unavailable or abstaining generation remains actionable. Editing inputs hides stale results; reset recomputes the zero-change comparison. Numeric field IDs resolve to their canonical code, preventing a valid response from being hidden. Pilot fields remain excluded.

Verification: TypeScript and targeted ESLint passed; four backend scenario tests passed. A mobile browser check used actual backend-generated responses from a disposable database with browser writes intercepted. It passed missing-baseline recovery, numeric field selection, cost reduction, three nutrient diagrams, heavy-rain blocking state, reset, stale-result removal, viewport width and page-error checks. No invented yield model or savings claim was added. No commit or push.
