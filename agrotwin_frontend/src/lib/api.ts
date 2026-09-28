/**
 * Typed client for the real AgroTwin backend (agrotwin_api/app/api/routes.py).
 * Every function here calls a real endpoint — no fabricated data lives in this file.
 */

export const API_BASE_URL = "/api/backend";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method || "GET").toUpperCase();
  const isRetryable = method === "GET" && !init?.signal?.aborted;

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: init?.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json", ...(init?.headers || {}) }
        : init?.headers,
      ...init,
    });
  } catch (err) {
    // A dev-server / connection hiccup throws before any response — a real
    // HTTP error (4xx/5xx) does not. One silent retry on a plain GET clears
    // the transient case instead of surfacing "Failed to fetch" to the user.
    if (!isRetryable || init?.signal?.aborted) throw err;
    await sleep(500);
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: init?.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json", ...(init?.headers || {}) }
        : init?.headers,
      ...init,
    });
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

// ─── Types (mirroring real response shapes from routes.py) ───────────────────

export interface FieldSummary {
  field_id: number;
  is_demo?: boolean;
  soil_health_score?: number | null;
  field_code: string;
  area_ha: number | null;
  lat: number | null;
  lon: number | null;
  soil_type: string | null;
  farmer_name: string | null;
  crop_code: string | null;
  current_stage: string | null;
}

export interface TwinNutrient {
  current: number | null;
  target: number | null;
  unit: string;
}

export interface TwinCurrentPlan {
  nextAction: string;
  fertilizerBreakdown: Record<string, number>;
  quantity: string;
  applicationWindow: string;
  estimatedCost: number | null;
  costCitation: string | null;
  pricesPerKg: Record<string, number> | null;
  confidence: string;
  citation: string;
  soilGap: Record<string, number>;
  status: string;
  reason: string | null;
  requiredActions: string[];
  flags: string[];
}

export interface TwinResponse {
  proof: RecommendationOut | null;
  nutrientBasis: string;
  conversionSource: string;
  fieldId: string;
  crop: string;
  growthStage: string;
  growthStageRaw: string;
  stageSequence: string[];
  area_ha: number;
  soilType: string | null;
  lat: number | null;
  lon: number | null;
  location: string | null;
  hasSoilTest: boolean;
  soilHealthScore: number | null;
  soilDetail: {
    ph: number | null;
    oc_percent: number | null;
    n_score: number | null;
    p_score: number | null;
    k_score: number | null;
  };
  nutrients: { n: TwinNutrient; p: TwinNutrient; k: TwinNutrient };
  currentPlan: TwinCurrentPlan;
  weather: {
    available: boolean;
    rainfall_mm_next_7d: number | null;
    heavy_rain_alert: boolean;
    condition: string | null;
  };
  waterStress: { label: string; reason: string };
  cropCondition: { label: string; reason: string };
  pestDiseaseRisk: { label: string; reason: string };
  overallStatus: string;
  activeAlert: { title: string; description: string } | null;
}

export interface WhatIfPlanSide {
  quantities: Record<string, number>;
  confidence: string;
  status: string;
  cost: number | null;
  costCurrency: string;
  costCitation: string;
  applicationWindow: string | null;
  rainfallMm: number | null;
  nutrientsSupplied: Record<string, number>;
  gap: Record<string, number>;
  excess: Record<string, number>;
  shortfall: Record<string, number>;
  validation: { is_valid: boolean; warnings: string[]; blocking_issues: string[] };
  sustainabilityNotes: string[];
}
export interface WhatIfResponse {
  fieldId: string;
  crop: string | null;
  status: 'SIMULATION' | 'NO_DATA' | 'ABSTAIN';
  reason: string | null;
  requiredActions: string[];
  original: WhatIfPlanSide | null;
  simulated: WhatIfPlanSide | null;
  deltaCost: number | null;
  deltaYield: null;
  yieldReason: string;
  notes: string[];
}

export interface Alert {
  alert_id: number;
  field_id: number;
  field_code?: string | null;
  alert_type: string;
  severity: string | null;
  message: string | null;
  triggered_at: string;
  resolved_at: string | null;
  related_recommendation_id: number | null;
}

export interface OcrExtractedField {
  value: number | string | null;
  confidence: number;
}

export interface SoilReportUploadResponse {
  status: string;
  upload_id: number | null;
  file_path: string | null;
  extracted_data: Record<string, OcrExtractedField>;
  fields_needing_review: string[];
  engine: string;
  message: string;
}

export interface SoilTestConfirmInput {
  p_basis?: "P" | "P2O5";
  k_basis?: "K" | "K2O";
  n_kg_ha?: number | null;
  p_kg_ha?: number | null;
  k_kg_ha?: number | null;
  ph?: number | null;
  oc_percent?: number | null;
  ec_ds_m?: number | null;
  test_date?: string | null;
  source?: "lab" | "ocr" | "manual";
}

export interface RecommendationOut {
  why?: { soil?: string; crop?: string; weather?: string; gap?: Record<string, number>; required?: Record<string, number>; normalized_soil?: Record<string, number>; history?: ApplicationCredit | null } | null;
  based_on?: { farm_data?: string[]; evidence?: EvidenceItem[]; citation?: string | null; cost_estimate?: number | null; cost_currency?: string; cost_citation?: string; application_history?: ApplicationCredit | null; conversion_source?: string } | null;
  ledger?: { normalized_soil?: Record<string, number>; required?: Record<string, number>; gap?: Record<string, number>; application_history?: ApplicationCredit; nutrient_units?: string };
  validation?: { is_valid: boolean; warnings: string[]; blocking_issues: string[] } | null;
  data_quality?: Record<string, boolean>;
  weather_context?: { status?: string; source?: string | null; rainfall_mm_next_7d?: number | null; flags?: string[] };
  status: string;
  what: string | null;
  how_much: Record<string, number> | null;
  when: string | null;
  confidence: string;
  reason: string | null;
  required_actions: string[];
  flags: string[];
  [key: string]: unknown;
}

export interface EvidenceItem { source_file?: string; citation?: string; excerpt?: string; content?: string; confidence?: string; score?: number; }
export interface ApplicationCredit {
  status: string; credits_kg_ha: Record<string, number> | null; source?: string | null; reason?: string;
  assumptions?: string[]; applications?: { application_id: number; application_date: string; product: string; status: string; credits_kg_ha?: Record<string, number> }[];
}
export interface FertilizerApplication { application_id: number; application_date: string; product_code: string; quantity_kg_ha: number; notes: string | null; }
export function getApplications(fieldId: string): Promise<{ status: string; applications: FertilizerApplication[] }> {
  return request(`/fields/${encodeURIComponent(fieldId)}/applications`);
}
export function getFertilizerProducts(): Promise<{ product_code: string; product_name: string }[]> {
  return request("/fertilizer-products");
}
export function recordApplication(fieldId: string, body: { product_code: string; application_date: string; quantity_kg_ha: number; notes?: string }): Promise<{status: string; application_id: number}> {
  return request(`/fields/${encodeURIComponent(fieldId)}/applications`, {method: "POST", body: JSON.stringify(body)});
}

// ─── API functions ─────────────────────────────────────────────────────────

export function getFields(demo = false): Promise<FieldSummary[]> {
  return request<FieldSummary[]>(demo ? "/fields?demo=true" : "/fields");
}

/**
 * Human-facing field label — never the routing key. Pilot demo codes
 * (REAL-001) are already meaningful and are kept as-is; real onboarded
 * fields get a stable "FARM-01" sequence number from their numeric id
 * instead of the random UUID baked into field_code.
 */
export function fieldDisplayName(fieldCode: string, fieldId?: number | null): string {
  if (!fieldCode || /^REAL-\d+$/.test(fieldCode)) return fieldCode;
  if (fieldId != null) return `FARM-${String(fieldId).padStart(2, "0")}`;
  return fieldCode;
}

export interface OnboardingOptions {
  stages: { crop_code: string; stage_name: string; region_id: number | null }[];
  districts: { district_id: number; region_id: number; district_name: string; region_name: string }[];
  crops: { crop_code: string; crop_name: string; recommendation_type: string }[];
}

export function getOnboardingOptions(): Promise<OnboardingOptions> {
  return request("/onboarding/options");
}

export function createFarmer(body: { region_id: number; full_name: string }): Promise<{ farmer_id: number }> {
  return request("/farmers", { method: "POST", body: JSON.stringify(body) });
}

export function createField(body: {
  region_id: number; district_id: number; farmer_id: number; field_code: string;
  area_ha: number; irrigation_type: string; lat: number | null; lon: number | null;
}): Promise<{ field_id: number }> {
  return request("/fields", { method: "POST", body: JSON.stringify(body) });
}

export function getTwin(fieldId: string, signal?: AbortSignal): Promise<TwinResponse> {
  return request<TwinResponse>(`/fields/${encodeURIComponent(fieldId)}/twin`, { signal });
}

export function recommend(
  fieldId: string,
  body?: { agents?: string[]; optimizer?: string; mock_weather?: Record<string, unknown> }
): Promise<RecommendationOut> {
  return request<RecommendationOut>(`/fields/${encodeURIComponent(fieldId)}/recommend`, {
    method: "POST",
    body: JSON.stringify(body || {}),
  });
}

export function getLatestRecommendation(fieldId: string): Promise<Record<string, unknown>> {
  return request(`/fields/${encodeURIComponent(fieldId)}/recommendations/latest`);
}

export interface RecommendationHistoryEntry {
  recommendation_id: number;
  generated_at: string;
  status: string;
  confidence: string | null;
  confidence_reason: string | null;
  total_cost_estimate: number | null;
  invalidated_at: string | null;
  superseded_by: number | null;
  what: string | null;
  how_much: Record<string, number> | null;
  when: string | null;
  reason: string | null;
}

export function getRecommendationHistory(fieldId: string, limit = 20): Promise<{ field_id: number; history: RecommendationHistoryEntry[] }> {
  return request(`/fields/${encodeURIComponent(fieldId)}/recommendations?limit=${limit}`);
}

export function getAlerts(fieldId: string): Promise<{ alerts: Alert[] }> {
  return request(`/fields/${encodeURIComponent(fieldId)}/alerts`);
}

export function getAllAlerts(limit = 50): Promise<Alert[]> {
  return request(`/alerts?limit=${limit}`);
}

export function whatIf(
  fieldId: string,
  body: { fertilizer_delta_pct?: number; rainfall_mm?: number; product_deltas_pct?: Record<string, number> }
): Promise<WhatIfResponse> {
  return request<WhatIfResponse>(`/fields/${encodeURIComponent(fieldId)}/what-if`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function uploadSoilReport(
  fieldId: string,
  file: File
): Promise<SoilReportUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<SoilReportUploadResponse>(
    `/fields/${encodeURIComponent(fieldId)}/soil-report/upload`,
    { method: "POST", body: form }
  );
}

export function confirmSoilReport(
  fieldId: string,
  body: { upload_id?: number | null; soil_test: SoilTestConfirmInput }
): Promise<{ status: string; message: string }> {
  return request(`/fields/${encodeURIComponent(fieldId)}/soil-report/confirm`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function overridePlan(
  fieldId: string,
  body: { recommendation_id: number; new_plan: Record<string, number>; reason: string; agronomist_id?: string }
): Promise<{ status: string; new_recommendation_id: number }> {
  return request(`/fields/${encodeURIComponent(fieldId)}/override`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function assignCrop(
  fieldId: string,
  body: {
    crop_code: string;
    variety?: string | null;
    sowing_date?: string | null;
    current_stage?: string | null;
    recommendation_type?: string | null;
    target_yield_kg_ha?: number | null;
  }
): Promise<{ status: string; field_id: number; crop_id: number; crop_code: string }> {
  return request(`/fields/${encodeURIComponent(fieldId)}/crop`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
