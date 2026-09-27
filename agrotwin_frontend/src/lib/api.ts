/**
 * Typed client for the real AgroTwin backend (agrotwin_api/app/api/routes.py).
 * Every function here calls a real endpoint — no fabricated data lives in this file.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: init?.body && !(init.body instanceof FormData)
      ? { "Content-Type": "application/json", ...(init?.headers || {}) }
      : init?.headers,
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

// ─── Types (mirroring real response shapes from routes.py) ───────────────────

export interface FieldSummary {
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
  current: number;
  target: number;
  unit: string;
}

export interface TwinCurrentPlan {
  nextAction: string;
  fertilizerBreakdown: Record<string, number>;
  quantity: string;
  applicationWindow: string;
  estimatedCost: number | null;
  costCitation: string | null;
  confidence: string;
  citation: string;
  soilGap: Record<string, number>;
  status: string;
  reason: string | null;
  requiredActions: string[];
  flags: string[];
}

export interface TwinResponse {
  fieldId: string;
  crop: string;
  growthStage: string;
  growthStageRaw: string;
  stageSequence: string[];
  area_ha: number;
  soilType: string | null;
  lat: number;
  lon: number;
  location: string;
  hasSoilTest: boolean;
  soilHealthScore: number;
  soilDetail: {
    ph: number | null;
    oc_percent: number | null;
    n_score: number;
    p_score: number;
    k_score: number;
  };
  nutrients: { n: TwinNutrient; p: TwinNutrient; k: TwinNutrient };
  currentPlan: TwinCurrentPlan;
  weather: {
    rainfall_mm_next_7d: number;
    heavy_rain_alert: boolean;
    condition: string;
  };
  activeAlert: { title: string; description: string } | null;
}

export interface WhatIfPlanSide {
  fertilizer: string;
  rainfall: string;
  yieldBand: string;
  confidence: string;
  cost: number;
  modelSignals: {
    growthStage: string;
    vigor: string;
    nutrientSufficiency: string;
    waterStress: string;
  };
}

export interface WhatIfResponse {
  crop: string;
  original: WhatIfPlanSide;
  simulated: WhatIfPlanSide;
}

export interface Alert {
  alert_id: number;
  field_id: number;
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

// ─── API functions ─────────────────────────────────────────────────────────

export function getFields(): Promise<FieldSummary[]> {
  return request<FieldSummary[]>("/fields");
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

export function getAlerts(fieldId: string): Promise<{ alerts: Alert[] }> {
  return request(`/fields/${encodeURIComponent(fieldId)}/alerts`);
}

export function whatIf(
  fieldId: string,
  body: { fertilizer_delta_pct?: number; rainfall_mm?: number }
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
