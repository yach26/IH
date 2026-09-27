# Verification results — 2026-09-27

## Subsequent onboarding fix

The farmer-first entry issue was fixed after the audit below. Unselected Dashboard, Upload and Simulator routes now render a farmer/field form and never auto-select the first field or REAL-001. The form saves farmer and field details using the existing creation APIs, assigns the selected crop, then opens soil upload. Supported location/crop choices come from a new read-only options endpoint. Pilot fields require explicit selection. The landing hero no longer loads pilot measurements, and the navigation no longer asserts Kolhapur as the user's location.

Field-specific components remount on selection changes, upload confirmation refetches the Twin, and simulator access requires confirmed soil and a recommendation. Missing stages and abstained fertilizer quantities no longer get defaults. Incomplete OCR confirmation now returns 422 and cross-field upload confirmation returns 404.

Validation: 146 backend tests passed; frontend typecheck and build passed; lint had no errors. Browser checks confirmed all three unselected pages make no Twin requests and explicit pilot selection still works. The older findings below describe the pre-fix audit and should not be treated as the current status of those corrected items. Remaining simulator fallback behavior, same-second recommendation ordering, and full end-to-end browser OCR verification still need separate follow-up.

The existing checks pass, but the implementation does not yet satisfy docs 17–20.
This pass verified and inspected the existing changes; it did not change application code.

## Repository checks

- `IH/.venv/Scripts/python.exe scripts/run_tests.py`: **143 passed**, 162.91 seconds. Network-enabled rerun included live weather, dense retrieval, and real OCR tests. The original sandboxed run was interrupted after network retries stalled model loading.
- `npm run lint`: **0 errors, 8 warnings** (seven image-element warnings and unused `isSimulating`).
- `npx tsc --noEmit`: passed.
- `npm run build`: passed. The first attempt compiled but hit sandbox `spawn EPERM`; the permitted rerun completed.

## Live HTTP scenarios

Used an actual Uvicorn server and HTTP client, a disposable SQLite copy of the existing local database, and `tests/fixtures/shc_sample_1.txt`. Existing pilot data was not modified. This is API verification, not browser interaction or a visual UI review. No mocked weather was supplied to recommendation generation; the heavy-rain event in I was explicitly simulated.

| Scenario | Result |
| --- | --- |
| A | New field has no soil, fertilizer, coordinates, or weather leakage. **Fails stage provenance:** returns `Grand Growth` without an assigned crop/stage. |
| B | Text OCR returns six extracted values and leaves soil unconfirmed. **Fails empty-plan representation:** crop assignment has already created an ABSTAIN record, which Twin formats as `DAP 0 + Urea 0 + MOP 0 kg/ha`. |
| C | Confirmation persists soil; a subsequent HTTP request returns the confirmed N/P/K. Existing monitoring also automatically replans on confirmation. |
| D | Passed after explicitly removing the new field's recommendations in the disposable copy to construct the confirmed-soil/no-plan state. Returns confirmed soil, `NO_DATA`, and an empty fertilizer breakdown. |
| E | Passed: pipeline generates a plan with successful validation, heuristic optimizer provenance, and retrieved evidence. |
| F | Independent requests reconstruct soil and plan after D/E. An earlier run with automatic and explicit recommendations generated within the same second returned `PLAN_REVISED` instead of the newly generated `PLAN_GENERATED`; latest-record ordering needs a deterministic tie-breaker. Browser refresh remains unverified. |
| G | Explicit `REAL-001` Twin response remained unchanged throughout new-field operations. |
| H | Unreadable report stays in OCR_FAILED review; unknown field returns 404. **Fails incomplete confirmation:** missing N/P/K raises an uncaught ValueError and returns HTTP 500. |
| I | Passed: heavy-rain injection produces an alert, invalidates the prior plan, and produces a revised recommendation. |

Reproduction script and detailed results are in `.cache/verify_doc18.py` and `.cache/doc18-results.json` (ignored local artifacts). The second run completed all checks but encountered a Windows temporary-file cleanup error; the script's missing connection close was corrected afterward.

## Remaining code-review findings

- `src/lib/useFieldParam.ts:7`: still defaults to `REAL-001`; the upload page uses this hook. Loading, empty, and failed field-list states can therefore retain the pilot ID.
- `src/app/simulator/page.tsx:196`: defaults to a pilot field, substitutes a crop preset for an absent recommendation baseline, and uses local simulation when the API fails. Baseline/result requests lack stale-response protection when fields change. A zero N gap is treated as missing.
- `src/app/upload/page.tsx`: no immediate Twin refetch after confirmation; no stale-response guard for an upload/confirmation completing after field selection changes. File acceptance is broader than the displayed PNG/JPG/PDF hint, and there is no explicit empty-field guard.
- `app/api/routes.py:218`: missing or null persisted fertilizer quantities become zero-valued DAP/Urea/MOP entries, including ABSTAIN records. These are live fallbacks, unlike legitimate product definitions and test fixtures.
- `app/api/routes.py:235`: missing/unsupported crop timelines use sugarcane stages and missing stages become GRAND_GROWTH.
- `app/api/routes.py:537`: confirmation resolves the URL field but does not verify that `upload_id` belongs to it before writing. This ownership issue was found by inspection, not exercised by a cross-field mutation.
- Latest recommendation queries order only by `generated_at`, allowing same-second records to return an older plan.

No commit or push was made. Full browser A–I verification and fixes for these findings remain outstanding.
