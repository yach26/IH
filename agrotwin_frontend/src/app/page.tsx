"use client";

import React, { useState, useEffect, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FieldMeta {
  field_id: number;
  field_code: string;
  area_ha: number;
  soil_type?: string;
  irrigation_type?: string;
  current_crop_id?: number;
  current_variety?: string;
  sowing_date?: string;
  current_stage?: string;
  recommendation_type?: string;
}

interface SoilData {
  soil_test_id?: number;
  test_date?: string;
  n_kg_ha?: number;
  p_kg_ha?: number;
  k_kg_ha?: number;
  ph?: number;
  oc_percent?: number;
  ec_ds_m?: number;
  source?: string;
}

interface RecommendationPlan {
  recommendation_id?: number;
  status?: string;
  what?: string;
  how_much?: Record<string, number>;
  when?: string;
  when_detail?: {
    code?: string;
    label?: string;
    window_start?: string;
    window_end?: string;
    revised?: boolean;
  };
  why?: {
    soil?: string;
    crop?: string;
    weather?: string;
    history?: string;
    gap?: Record<string, number>;
    required?: Record<string, number>;
  };
  based_on?: {
    evidence?: Array<{
      source_file?: string;
      excerpt?: string;
      score?: number;
      citation?: string;
    }>;
    citation?: string;
    optimizer?: string;
    cost_estimate?: number;
    cost_currency?: string;
    cost_citation?: string;
  };
  confidence?: string;
  flags?: string[];
  data_quality?: Record<string, boolean>;
  validation?: {
    is_valid?: boolean;
    warnings?: string[];
    blocking_issues?: string[];
  };
  status_db?: string;
  invalidated_at?: string;
}

interface FarmAlert {
  alert_type?: string;
  severity?: string;
  message?: string;
  triggered_at?: string;
}

interface OcrValue {
  value: number | null;
  confidence: number;
}

interface OcrUpload {
  upload_id?: number;
  engine?: string;
  extracted_data?: Record<string, OcrValue>;
}

interface WhatIfResult {
  original_plan?: RecommendationPlan;
  simulated_plan?: RecommendationPlan;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default function AgroTwinDashboard() {
  const [selectedFieldId, setSelectedFieldId] = useState<string>("1");
  const [activeTab, setActiveTab] = useState<"dashboard" | "whatif" | "ocr" | "crop" | "agronomist">("dashboard");

  // Twin state
  const [fieldData, setFieldData] = useState<FieldMeta | null>(null);
  const [soilData, setSoilData] = useState<SoilData | null>(null);
  const [latestPlan, setLatestPlan] = useState<RecommendationPlan | null>(null);
  const [alerts, setAlerts] = useState<FarmAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [showProof, setShowProof] = useState<boolean>(false);
  const [selectedOptimizer, setSelectedOptimizer] = useState<string>("heuristic");

  // What-If State
  const [whatIfFertDelta, setWhatIfFertDelta] = useState<number>(0);
  const [whatIfRainfall, setWhatIfRainfall] = useState<number>(0);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResult | null>(null);
  const [whatIfLoading, setWhatIfLoading] = useState<boolean>(false);

  // OCR Upload State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<OcrUpload | null>(null);
  const [ocrLoading, setOcrLoading] = useState<boolean>(false);
  const [confirmValues, setConfirmValues] = useState<Record<string, number | string>>({
    n_kg_ha: 150,
    p_kg_ha: 30,
    k_kg_ha: 220,
    ph: 7.4,
    oc_percent: 0.55,
    ec_ds_m: 0.4,
  });

  // Crop Setup State
  const [cropForm, setCropForm] = useState({
    crop_code: "BANANA",
    variety: "Grand Naine",
    sowing_date: "2025-07-15",
    current_stage: "Vegetative (4 months)",
    recommendation_type: "FULL_SEASON",
  });

  // Agronomist Override State
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideDap, setOverrideDap] = useState<number>(200);
  const [overrideUrea, setOverrideUrea] = useState<number>(100);
  const [overrideMop, setOverrideMop] = useState<number>(150);
  const activeFetch = useRef<AbortController | null>(null);

  const fetchTwinData = async (fId: string) => {
    activeFetch.current?.abort();
    const controller = new AbortController();
    activeFetch.current = controller;
    const { signal } = controller;
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await fetch(`${API_BASE}/fields/${fId}/twin`, { signal });
      if (res.ok) {
        const data = await res.json();
        setFieldData(data.field);
        setSoilData(data.soil);
        setLatestPlan(data.latest_plan);
      } else {
        setActionMessage(`Error loading twin for field ${fId}`);
      }

      const alertRes = await fetch(`${API_BASE}/fields/${fId}/alerts`, { signal });
      if (alertRes.ok) {
        const aData = await alertRes.json();
        setAlerts(aData.alerts || []);
      }
    } catch (e: unknown) {
      if (!signal.aborted) setActionMessage(`Network error connecting to API (${API_BASE}): ${errorMessage(e)}`);
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  };

  useEffect(() => {
    // Initial subscription; field switches trigger their fetch in the handler.
    const timer = window.setTimeout(() => { void fetchTwinData("1"); }, 0);
    return () => {
      window.clearTimeout(timer);
      activeFetch.current?.abort();
    };
  }, []);

  // Request new recommendation
  const handleRecommend = async () => {
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ optimizer: selectedOptimizer }),
      });
      if (res.ok) {
        const plan = await res.json();
        setLatestPlan(plan);
        setActionMessage(`Recommendation generated successfully using ${selectedOptimizer} optimizer!`);
        fetchTwinData(selectedFieldId);
      } else {
        const err = await res.json();
        setActionMessage(`Failed: ${err.detail || "Error generating recommendation"}`);
      }
    } catch (e: unknown) {
      setActionMessage(`Error: ${errorMessage(e)}`);
    } finally {
      setLoading(false);
    }
  };

  // Inject Heavy Rain Alert (Demo WOW Path)
  const handleTriggerHeavyRain = async () => {
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await fetch(`${API_BASE}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: "HEAVY_RAIN_ALERT",
          field_id: parseInt(selectedFieldId),
          payload: {
            heavy_rain_alert: true,
            rainfall_probability: 95,
            rainfall_mm_next_7d: 85.0,
          },
        }),
      });
      if (res.ok) {
        setActionMessage(
          `HEAVY_RAIN_ALERT event injected! Active plan was invalidated and rescheduled away from rain window.`
        );
        fetchTwinData(selectedFieldId);
      } else {
        const err = await res.json();
        setActionMessage(`Error injecting event: ${err.detail}`);
      }
    } catch (e: unknown) {
      setActionMessage(`Network error: ${errorMessage(e)}`);
    } finally {
      setLoading(false);
    }
  };

  // Run What-If
  const handleRunWhatIf = async () => {
    setWhatIfLoading(true);
    try {
      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/what-if`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fertilizer_delta_pct: whatIfFertDelta,
          rainfall_mm: whatIfRainfall,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setWhatIfResult(data);
      } else {
        alert("What-If simulation failed");
      }
    } catch (e: unknown) {
      alert(`Simulation error: ${errorMessage(e)}`);
    } finally {
      setWhatIfLoading(false);
    }
  };

  // Handle OCR file upload
  const handleUploadFile = async () => {
    if (!uploadFile) return;
    setOcrLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);

      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/soil-report/upload`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data: OcrUpload = await res.json();
        setUploadResult(data);
        if (data.extracted_data) {
          const vals: Record<string, number | string> = {};
          for (const [k, v] of Object.entries(data.extracted_data)) {
            vals[k] = v.value ?? "";
          }
          setConfirmValues((prev) => ({ ...prev, ...vals }));
        }
      } else {
        alert("Failed to upload report");
      }
    } catch (e: unknown) {
      alert(`Upload error: ${errorMessage(e)}`);
    } finally {
      setOcrLoading(false);
    }
  };

  // Confirm OCR Values
  const handleConfirmOcr = async () => {
    setOcrLoading(true);
    try {
      const payload = {
        upload_id: uploadResult?.upload_id,
        soil_test: {
          n_kg_ha: parseFloat(String(confirmValues.n_kg_ha)) || 0,
          p_kg_ha: parseFloat(String(confirmValues.p_kg_ha)) || 0,
          k_kg_ha: parseFloat(String(confirmValues.k_kg_ha)) || 0,
          ph: parseFloat(String(confirmValues.ph)) || 7.0,
          oc_percent: parseFloat(String(confirmValues.oc_percent)) || 0.5,
          ec_ds_m: parseFloat(String(confirmValues.ec_ds_m)) || 0.3,
          source: "ocr",
          test_date: new Date().toISOString().split("T")[0],
        },
      };

      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/soil-report/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        alert("Soil report confirmed! Twin updated and SOIL_REPORT_UPDATED event emitted.");
        fetchTwinData(selectedFieldId);
        setActiveTab("dashboard");
      } else {
        alert("Confirmation failed");
      }
    } catch (e: unknown) {
      alert(`Error: ${errorMessage(e)}`);
    } finally {
      setOcrLoading(false);
    }
  };

  // Assign Crop
  const handleAssignCrop = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/crop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cropForm),
      });
      if (res.ok) {
        setActionMessage(`Crop ${cropForm.crop_code} successfully assigned to Field ${selectedFieldId}!`);
        fetchTwinData(selectedFieldId);
        setActiveTab("dashboard");
      } else {
        const err = await res.json();
        alert(`Failed: ${err.detail || "Error assigning crop"}`);
      }
    } catch (e: unknown) {
      alert(`Error: ${errorMessage(e)}`);
    } finally {
      setLoading(false);
    }
  };

  // Agronomist Override
  const handleAgronomistOverride = async () => {
    if (!latestPlan?.recommendation_id) {
      alert("No active recommendation to override.");
      return;
    }
    try {
      const overridePlan = {
        ...latestPlan,
        what: "Custom Agronomist Blend",
        how_much: {
          DAP_kg_ha: overrideDap,
          UREA_kg_ha: overrideUrea,
          MOP_kg_ha: overrideMop,
        },
        confidence: "HIGH",
      };

      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recommendation_id: latestPlan.recommendation_id,
          reason: overrideReason || "Agronomist adjusted based on local canopy observation",
          agronomist_id: "agronomist-maharashtra-1",
          new_plan: overridePlan,
        }),
      });

      if (res.ok) {
        alert("Override applied successfully! Logged to immutable audit trail.");
        fetchTwinData(selectedFieldId);
        setActiveTab("dashboard");
      } else {
        alert("Override failed");
      }
    } catch (e: unknown) {
      alert(`Error: ${errorMessage(e)}`);
    }
  };

  const getConfidenceBadgeClass = (conf?: string) => {
    switch (conf?.toUpperCase()) {
      case "HIGH":
        return "badge badge-high";
      case "MEDIUM":
        return "badge badge-medium";
      case "LOW":
        return "badge badge-low";
      case "ABSTAIN":
        return "badge badge-abstain";
      default:
        return "badge badge-medium";
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Top Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold tracking-tight text-ink-primary">AgroTwin AI</span>
            <span className="badge badge-high">Live Twin</span>
          </div>
          <p className="text-sm text-ink-secondary mt-1">
            Evidence-Grounded Sustainable Fertilizer Optimizer &bull; Maharashtra Pilot (Kolhapur &amp; Jalgaon)
          </p>
        </div>

        {/* Field Selector */}
        <div className="mt-4 md:mt-0 flex items-center gap-3">
          <label htmlFor="field-select" className="text-sm font-medium text-ink-secondary">
            Select Field:
          </label>
          <select
            id="field-select"
            value={selectedFieldId}
            onChange={(e) => {
              setSelectedFieldId(e.target.value);
              void fetchTwinData(e.target.value);
            }}
            className="input-clean font-medium max-w-[240px]"
          >
            <option value="1">Field 1: SYN-001 (Banana, Jalgaon)</option>
            <option value="2">Field 2: SYN-002 (Banana, Jalgaon)</option>
            <option value="3">Field 3: SYN-003 (Sugarcane, Kolhapur)</option>
            <option value="4">Field 4: SYN-004 (Sugarcane, Kolhapur)</option>
            <option value="5">Field 5: SYN-005 (Cotton, Jalgaon)</option>
            <option value="6">Field 6: SYN-006 (Soybean, Kolhapur)</option>
            <option value="7">Field 7: SYN-007 (Cotton, Jalgaon)</option>
            <option value="8">Field 8: SYN-008 (Sugarcane, Kolhapur)</option>
          </select>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="flex flex-wrap gap-2 border-b border-border pb-3 mb-6" aria-label="Views">
        <button
          onClick={() => setActiveTab("dashboard")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "dashboard"
              ? "bg-agri-primary text-white"
              : "bg-white text-ink-secondary hover:bg-bg-subtle"
          }`}
        >
          Dashboard &amp; Plan
        </button>
        <button
          onClick={() => setActiveTab("whatif")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "whatif"
              ? "bg-agri-primary text-white"
              : "bg-white text-ink-secondary hover:bg-bg-subtle"
          }`}
        >
          What-If Simulator
        </button>
        <button
          onClick={() => setActiveTab("ocr")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "ocr"
              ? "bg-agri-primary text-white"
              : "bg-white text-ink-secondary hover:bg-bg-subtle"
          }`}
        >
          Soil Report OCR
        </button>
        <button
          onClick={() => setActiveTab("crop")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "crop"
              ? "bg-agri-primary text-white"
              : "bg-white text-ink-secondary hover:bg-bg-subtle"
          }`}
        >
          Crop Assignment
        </button>
        <button
          onClick={() => setActiveTab("agronomist")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "agronomist"
              ? "bg-agri-primary text-white"
              : "bg-white text-ink-secondary hover:bg-bg-subtle"
          }`}
        >
          Agronomist Review
        </button>
      </nav>

      {/* Global Status Banner */}
      {actionMessage && (
        <div className="mb-6 p-4 rounded-lg bg-agri-light text-agri-primary border border-agri-primary/20 text-sm font-medium flex items-center justify-between">
          <span>{actionMessage}</span>
          <button
            onClick={() => setActionMessage(null)}
            className="text-agri-primary hover:text-agri-hover font-bold ml-4"
          >
            &times;
          </button>
        </div>
      )}

      {loading && (
        <div className="py-12 text-center text-ink-secondary">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm font-medium">Syncing with Digital Twin...</p>
        </div>
      )}

      {!loading && activeTab === "dashboard" && (
        <div className="space-y-6">
          {/* Active Alerts Banner */}
          {alerts && alerts.length > 0 && (
            <div className="p-4 rounded-xl border border-amber-300 bg-amber-50">
              <div className="flex items-center gap-2 text-amber-800 font-semibold text-sm">
                <span>&#9888; Active Farm Alerts ({alerts.length})</span>
              </div>
              <div className="mt-2 space-y-1">
                {alerts.map((a, idx) => (
                  <p key={idx} className="text-xs text-amber-900">
                    &bull; <strong className="uppercase">{a.alert_type}</strong> ({a.severity}): {a.message}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Primary Recommendation Card (Hero) */}
          <div className="card-clean border-2 border-agri-primary/30">
            <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-border gap-4">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Current Active Plan &bull; Field {fieldData?.field_code || selectedFieldId}
                </span>
                <h2 className="text-2xl font-bold text-ink-primary mt-1">
                  {latestPlan?.what || "No Application Scheduled"}
                </h2>
              </div>
              <div className="flex items-center gap-3">
                <span className={getConfidenceBadgeClass(latestPlan?.confidence)}>
                  Confidence: {latestPlan?.confidence || "UNKNOWN"}
                </span>
                {latestPlan?.status_db && (
                  <span className="badge bg-zinc-100 text-zinc-800 border border-zinc-200">
                    Status: {latestPlan.status_db}
                  </span>
                )}
              </div>
            </div>

            {/* Prescribed Quantities */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-6 border-b border-border">
              <div>
                <span className="text-xs font-medium text-ink-secondary">Nutrient Requirements (Gap Met)</span>
                <div className="mt-2 space-y-2">
                  {latestPlan?.how_much && Object.keys(latestPlan.how_much).length > 0 ? (
                    Object.entries(latestPlan.how_much).map(([k, v]) => (
                      <div key={k} className="flex justify-between items-center text-sm py-1 border-b border-zinc-100">
                        <span className="font-medium text-ink-primary">{k.replace("_kg_ha", "")}</span>
                        <span className="font-semibold text-agri-primary">{v} kg/ha</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-ink-muted">No nutrient deficit requiring chemical fertilizer.</p>
                  )}
                </div>
              </div>

              <div>
                <span className="text-xs font-medium text-ink-secondary">Application Window</span>
                <p className="text-sm font-semibold text-ink-primary mt-2">
                  {latestPlan?.when || "Pending assessment"}
                </p>
                {latestPlan?.when_detail?.revised && (
                  <p className="text-xs text-amber-700 mt-1">
                    &#9888; Application timing revised due to heavy rain forecast.
                  </p>
                )}
              </div>

              <div>
                <span className="text-xs font-medium text-ink-secondary">Estimated Investment</span>
                <p className="text-xl font-bold text-ink-primary mt-2">
                  {latestPlan?.based_on?.cost_estimate
                    ? `₹${latestPlan.based_on.cost_estimate.toLocaleString()}`
                    : "₹0"}
                </p>
                <p className="text-xs text-ink-muted mt-1">
                  {latestPlan?.based_on?.cost_citation || "Based on FCO regional price model"}
                </p>
              </div>
            </div>

            {/* Actions Toolbar */}
            <div className="pt-4 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <button onClick={() => setShowProof(!showProof)} className="btn-secondary">
                  {showProof ? "Hide Evidence Proof &darr;" : "Why This Plan? (Proof &amp; Evidence) &rarr;"}
                </button>
                <button onClick={() => setActiveTab("whatif")} className="btn-secondary">
                  Simulate What-If
                </button>
              </div>

              <div className="flex items-center gap-3">
                <select
                  value={selectedOptimizer}
                  onChange={(e) => setSelectedOptimizer(e.target.value)}
                  className="input-clean text-xs py-1.5 px-2 max-w-[170px]"
                >
                  <option value="heuristic">Optimizer: Heuristic</option>
                  <option value="linprog">Optimizer: Linprog (LP)</option>
                </select>

                <button onClick={handleRecommend} className="btn-primary">
                  Re-evaluate Plan
                </button>

                <button
                  onClick={handleTriggerHeavyRain}
                  className="bg-amber-600 hover:bg-amber-700 text-white px-3 py-2 rounded-lg text-xs font-medium transition"
                  title="Simulate sudden heavy rainfall to watch real-time plan invalidation and rescheduling"
                >
                  &#9748; Test Heavy Rain Event
                </button>
              </div>
            </div>

            {/* Expandable Why This Plan (Proof Object) */}
            {showProof && (
              <div className="mt-6 pt-6 border-t border-border space-y-6">
                <div>
                  <h3 className="text-base font-bold text-ink-primary mb-3">
                    Proof-Carrying Recommendation &bull; Six Core Questions
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-bg-subtle text-xs space-y-1">
                      <strong className="text-ink-primary block">1. WHAT &amp; HOW MUCH:</strong>
                      <p className="text-ink-secondary">
                        {latestPlan?.what} — {JSON.stringify(latestPlan?.how_much || {})}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-bg-subtle text-xs space-y-1">
                      <strong className="text-ink-primary block">2. WHEN:</strong>
                      <p className="text-ink-secondary">{latestPlan?.when}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-bg-subtle text-xs space-y-1">
                      <strong className="text-ink-primary block">3. WHY:</strong>
                      <p className="text-ink-secondary">
                        Soil: {latestPlan?.why?.soil || "N/A"} | Crop: {latestPlan?.why?.crop || "N/A"}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-bg-subtle text-xs space-y-1">
                      <strong className="text-ink-primary block">4. BASED ON WHAT (Citations):</strong>
                      <p className="text-ink-secondary">
                        {latestPlan?.based_on?.citation || "MPKV / ICAR RDF Handbook"}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-bg-subtle text-xs space-y-1">
                      <strong className="text-ink-primary block">5. HOW SURE ARE WE:</strong>
                      <p className="text-ink-secondary">
                        Confidence: {latestPlan?.confidence} | Flags: {latestPlan?.flags?.join(", ") || "None"}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-bg-subtle text-xs space-y-1">
                      <strong className="text-ink-primary block">6. VALIDATION RULES:</strong>
                      <p className="text-ink-secondary">
                        Passed agronomic bounds checks: {latestPlan?.validation?.is_valid ? "YES" : "WARNINGS"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Evidence Chunks from Agentic RAG */}
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-secondary mb-2">
                    Evidence Chunks Retrieved via Hybrid RAG (BM25 + Dense)
                  </h4>
                  {latestPlan?.based_on?.evidence && latestPlan.based_on.evidence.length > 0 ? (
                    <div className="space-y-2">
                      {latestPlan.based_on.evidence.map((chunk, i) => (
                        <div key={i} className="p-3 rounded-lg border border-border bg-white text-xs">
                          <div className="flex justify-between items-center font-medium text-agri-primary mb-1">
                            <span>Source: {chunk.source_file || chunk.citation}</span>
                            <span className="text-ink-muted">Score: {chunk.score}</span>
                          </div>
                          <p className="text-ink-secondary line-clamp-3">{chunk.excerpt}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-ink-muted">No evidence chunks indexed for current query context.</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Farm State Summary (Twin & Soil) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Active Crop State */}
            <div className="card-clean">
              <h3 className="text-base font-bold text-ink-primary mb-4">Active Crop State</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Crop</span>
                  <span className="font-semibold text-ink-primary">{fieldData?.current_variety || "Banana (Grand Naine)"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Growth Stage</span>
                  <span className="font-semibold text-ink-primary">{fieldData?.current_stage || "Not set"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Sowing Date</span>
                  <span className="font-semibold text-ink-primary">{fieldData?.sowing_date || "N/A"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Recommendation Pattern</span>
                  <span className="font-semibold text-ink-primary">{fieldData?.recommendation_type || "FULL_SEASON"}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-ink-secondary">Field Area</span>
                  <span className="font-semibold text-ink-primary">{fieldData?.area_ha} Hectares</span>
                </div>
              </div>
            </div>

            {/* Soil Health Status */}
            <div className="card-clean">
              <h3 className="text-base font-bold text-ink-primary mb-4">Soil Test Metrics</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>Available Nitrogen (N)</span>
                    <span className="font-bold">{soilData?.n_kg_ha ?? "--"} kg/ha</span>
                  </div>
                  <div className="w-full bg-zinc-100 rounded-full h-2">
                    <div
                      className="bg-agri-primary h-2 rounded-full"
                      style={{ width: `${Math.min(100, ((soilData?.n_kg_ha || 0) / 250) * 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>Available Phosphorus (P)</span>
                    <span className="font-bold">{soilData?.p_kg_ha ?? "--"} kg/ha</span>
                  </div>
                  <div className="w-full bg-zinc-100 rounded-full h-2">
                    <div
                      className="bg-agri-primary h-2 rounded-full"
                      style={{ width: `${Math.min(100, ((soilData?.p_kg_ha || 0) / 60) * 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>Available Potassium (K)</span>
                    <span className="font-bold">{soilData?.k_kg_ha ?? "--"} kg/ha</span>
                  </div>
                  <div className="w-full bg-zinc-100 rounded-full h-2">
                    <div
                      className="bg-agri-primary h-2 rounded-full"
                      style={{ width: `${Math.min(100, ((soilData?.k_kg_ha || 0) / 450) * 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-zinc-100 text-xs text-ink-secondary">
                  <div>
                    <span>Soil pH: </span>
                    <strong className="text-ink-primary">{soilData?.ph ?? "--"}</strong>
                  </div>
                  <div>
                    <span>Organic Carbon (OC): </span>
                    <strong className="text-ink-primary">{soilData?.oc_percent ?? "--"}%</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* What-If Simulator Tab */}
      {!loading && activeTab === "whatif" && (
        <div className="space-y-6">
          <div className="card-clean">
            <h2 className="text-xl font-bold text-ink-primary mb-2">What-If Farm Condition Simulator</h2>
            <p className="text-sm text-ink-secondary mb-6">
              Simulate variations in fertilizer application or weather forecast changes to observe the Digital Twin&apos;s recalculation without modifying saved farm data.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-4">
              <div>
                <label className="text-sm font-semibold text-ink-primary block mb-2">
                  Fertilizer Rate Adjustment: {whatIfFertDelta > 0 ? `+${whatIfFertDelta}` : whatIfFertDelta}%
                </label>
                <input
                  type="range"
                  min="-50"
                  max="50"
                  step="5"
                  value={whatIfFertDelta}
                  onChange={(e) => setWhatIfFertDelta(parseInt(e.target.value))}
                  className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-ink-muted mt-1">
                  <span>-50% (Eco-reduction)</span>
                  <span>0% (Standard)</span>
                  <span>+50% (High-input)</span>
                </div>
              </div>

              <div>
                <label className="text-sm font-semibold text-ink-primary block mb-2">
                  Forecast Rainfall in Next 7 Days: {whatIfRainfall} mm
                </label>
                <input
                  type="range"
                  min="0"
                  max="120"
                  step="5"
                  value={whatIfRainfall}
                  onChange={(e) => setWhatIfRainfall(parseInt(e.target.value))}
                  className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-ink-muted mt-1">
                  <span>0 mm (Dry)</span>
                  <span>40 mm (Moderate)</span>
                  <span>&gt;60 mm (Heavy rain alert)</span>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button onClick={handleRunWhatIf} disabled={whatIfLoading} className="btn-primary">
                {whatIfLoading ? "Running Simulation..." : "Run What-If Analysis"}
              </button>
            </div>
          </div>

          {/* Simulation Output Comparison */}
          {whatIfResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card-clean border-zinc-200">
                <span className="badge bg-zinc-100 text-zinc-800 mb-2">Baseline Plan</span>
                <h3 className="text-lg font-bold text-ink-primary">
                  {whatIfResult.original_plan?.what || "Current Plan"}
                </h3>
                <div className="mt-4 space-y-2 text-sm">
                  {whatIfResult.original_plan?.how_much &&
                    Object.entries(whatIfResult.original_plan.how_much).map(([k, v]) => (
                      <div key={k} className="flex justify-between py-1 border-b border-zinc-100">
                        <span>{k.replace("_kg_ha", "")}</span>
                        <strong className="text-ink-primary">{Number(v)} kg/ha</strong>
                      </div>
                    ))}
                </div>
              </div>

              <div className="card-clean border-2 border-agri-primary bg-agri-light/20">
                <span className="badge badge-high mb-2">Simulated Outcome</span>
                <h3 className="text-lg font-bold text-agri-primary">
                  {whatIfResult.simulated_plan?.what || "Simulated Plan"}
                </h3>
                <div className="mt-4 space-y-2 text-sm">
                  {whatIfResult.simulated_plan?.how_much &&
                    Object.entries(whatIfResult.simulated_plan.how_much).map(([k, v]) => (
                      <div key={k} className="flex justify-between py-1 border-b border-zinc-100">
                        <span>{k.replace("_kg_ha", "")}</span>
                        <strong className="text-agri-primary">{Number(v)} kg/ha</strong>
                      </div>
                    ))}
                </div>
                <div className="mt-4 pt-3 border-t border-agri-primary/20 text-xs text-ink-secondary">
                  <strong>Simulated Timing:</strong> {whatIfResult.simulated_plan?.when}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Soil Report OCR Tab */}
      {!loading && activeTab === "ocr" && (
        <div className="space-y-6">
          <div className="card-clean">
            <h2 className="text-xl font-bold text-ink-primary mb-2">Soil Report OCR &amp; Verification</h2>
            <p className="text-sm text-ink-secondary mb-6">
              Upload a soil health card or lab report. Extracted values must be verified and confirmed by the farmer before any updates are committed to the Digital Twin.
            </p>

            <div className="border-2 border-dashed border-border rounded-xl p-8 text-center bg-bg-subtle/50">
              <input
                type="file"
                id="soil-file"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="hidden"
                accept=".txt,.pdf,.csv,.png,.jpg,.jpeg"
              />
              <label htmlFor="soil-file" className="cursor-pointer inline-flex flex-col items-center">
                <span className="text-3xl mb-2">&#128196;</span>
                <span className="btn-secondary text-xs mb-2">Choose Soil Report File</span>
                <span className="text-xs text-ink-muted">
                  {uploadFile ? uploadFile.name : "Select a lab text report, CSV, PDF, or image"}
                </span>
              </label>

              {uploadFile && (
                <div className="mt-4">
                  <button onClick={handleUploadFile} disabled={ocrLoading} className="btn-primary text-xs">
                    {ocrLoading ? "Extracting..." : "Upload &amp; Run OCR Extraction"}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Extracted Values & Confirmation Form */}
          {uploadResult && (
            <div className="card-clean border-2 border-border">
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div>
                  <h3 className="text-lg font-bold text-ink-primary">Extracted Soil Metrics</h3>
                  <p className="text-xs text-ink-muted">Extractor Engine: {uploadResult.engine}</p>
                </div>
                <span className="badge badge-medium">Farmer Verification Required</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-6">
                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">
                    Available Nitrogen (kg/ha)
                  </label>
                  <input
                    type="number"
                    value={confirmValues.n_kg_ha}
                    onChange={(e) => setConfirmValues({ ...confirmValues, n_kg_ha: e.target.value })}
                    className="input-clean"
                  />
                  <span className="text-[10px] text-ink-muted mt-1 block">
                    Confidence: {uploadResult.extracted_data?.n_kg_ha?.confidence ?? "0.92"}
                  </span>
                </div>

                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">
                    Available Phosphorus (kg/ha)
                  </label>
                  <input
                    type="number"
                    value={confirmValues.p_kg_ha}
                    onChange={(e) => setConfirmValues({ ...confirmValues, p_kg_ha: e.target.value })}
                    className="input-clean"
                  />
                  <span className="text-[10px] text-ink-muted mt-1 block">
                    Confidence: {uploadResult.extracted_data?.p_kg_ha?.confidence ?? "0.92"}
                  </span>
                </div>

                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">
                    Available Potassium (kg/ha)
                  </label>
                  <input
                    type="number"
                    value={confirmValues.k_kg_ha}
                    onChange={(e) => setConfirmValues({ ...confirmValues, k_kg_ha: e.target.value })}
                    className="input-clean"
                  />
                  <span className="text-[10px] text-ink-muted mt-1 block">
                    Confidence: {uploadResult.extracted_data?.k_kg_ha?.confidence ?? "0.92"}
                  </span>
                </div>

                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">Soil pH</label>
                  <input
                    type="number"
                    step="0.1"
                    value={confirmValues.ph}
                    onChange={(e) => setConfirmValues({ ...confirmValues, ph: e.target.value })}
                    className="input-clean"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">Organic Carbon (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={confirmValues.oc_percent}
                    onChange={(e) => setConfirmValues({ ...confirmValues, oc_percent: e.target.value })}
                    className="input-clean"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">
                    Electrical Conductivity (dS/m)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={confirmValues.ec_ds_m}
                    onChange={(e) => setConfirmValues({ ...confirmValues, ec_ds_m: e.target.value })}
                    className="input-clean"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border flex justify-end gap-3">
                <button onClick={() => setUploadResult(null)} className="btn-secondary">
                  Cancel
                </button>
                <button onClick={handleConfirmOcr} disabled={ocrLoading} className="btn-primary">
                  {ocrLoading ? "Updating Twin..." : "Confirm &amp; Update Digital Twin"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Crop Assignment Tab */}
      {!loading && activeTab === "crop" && (
        <div className="card-clean max-w-xl mx-auto">
          <h2 className="text-xl font-bold text-ink-primary mb-2">Field Crop Assignment</h2>
          <p className="text-sm text-ink-secondary mb-6">
            Update or assign the active crop for Field {selectedFieldId}. Changes emit a CROP_STAGE_CHANGED event and prompt re-evaluation.
          </p>

          <form onSubmit={handleAssignCrop} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-ink-secondary block mb-1">Crop Type</label>
              <select
                value={cropForm.crop_code}
                onChange={(e) => setCropForm({ ...cropForm, crop_code: e.target.value })}
                className="input-clean"
              >
                <option value="BANANA">Banana</option>
                <option value="SUGARCANE">Sugarcane</option>
                <option value="COTTON">Cotton</option>
                <option value="SOYBEAN">Soybean</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-ink-secondary block mb-1">Variety</label>
              <input
                type="text"
                value={cropForm.variety}
                onChange={(e) => setCropForm({ ...cropForm, variety: e.target.value })}
                className="input-clean"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-ink-secondary block mb-1">Sowing Date</label>
              <input
                type="date"
                value={cropForm.sowing_date}
                onChange={(e) => setCropForm({ ...cropForm, sowing_date: e.target.value })}
                className="input-clean"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-ink-secondary block mb-1">Current Growth Stage</label>
              <input
                type="text"
                value={cropForm.current_stage}
                onChange={(e) => setCropForm({ ...cropForm, current_stage: e.target.value })}
                className="input-clean"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-ink-secondary block mb-1">
                Recommendation Pattern (RDF Mode)
              </label>
              <select
                value={cropForm.recommendation_type}
                onChange={(e) => setCropForm({ ...cropForm, recommendation_type: e.target.value })}
                className="input-clean"
              >
                <option value="FULL_SEASON">FULL_SEASON (Standard cycle)</option>
                <option value="PRE_SEASONAL">PRE_SEASONAL (e.g. Sugarcane adsali)</option>
                <option value="RATOON">RATOON (Sugarcane ratoon)</option>
                <option value="IRRIGATED">IRRIGATED (Cotton irrigated)</option>
                <option value="RAINFED">RAINFED (Cotton rainfed)</option>
              </select>
            </div>

            <div className="pt-4 flex justify-end">
              <button type="submit" className="btn-primary">
                Save &amp; Activate Crop
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Agronomist Review & Override Tab */}
      {!loading && activeTab === "agronomist" && (
        <div className="space-y-6">
          <div className="card-clean">
            <h2 className="text-xl font-bold text-ink-primary mb-2">Agronomist Oversight &amp; Expert Override</h2>
            <p className="text-sm text-ink-secondary mb-6">
              Review automated recommendations and submit human-in-the-loop overrides. All overrides are logged to the immutable audit trail and published to the event bus.
            </p>

            <div className="p-4 rounded-lg bg-zinc-50 border border-zinc-200 mb-6 text-xs space-y-2">
              <div className="flex justify-between">
                <span>Field Code:</span>
                <strong>{fieldData?.field_code}</strong>
              </div>
              <div className="flex justify-between">
                <span>Current Automated Recommendation ID:</span>
                <strong>{latestPlan?.recommendation_id ?? "None"}</strong>
              </div>
              <div className="flex justify-between">
                <span>System Confidence:</span>
                <span className={getConfidenceBadgeClass(latestPlan?.confidence)}>{latestPlan?.confidence}</span>
              </div>
            </div>

            <div className="space-y-4 max-w-lg">
              <div>
                <label className="text-xs font-semibold text-ink-secondary block mb-1">
                  Agronomist Justification / Reason:
                </label>
                <textarea
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="e.g. Adjusted potassium application upward by 20% due to visible leaf deficiency signs."
                  className="input-clean"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">DAP (kg/ha)</label>
                  <input
                    type="number"
                    value={overrideDap}
                    onChange={(e) => setOverrideDap(parseFloat(e.target.value) || 0)}
                    className="input-clean"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">Urea (kg/ha)</label>
                  <input
                    type="number"
                    value={overrideUrea}
                    onChange={(e) => setOverrideUrea(parseFloat(e.target.value) || 0)}
                    className="input-clean"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-ink-secondary block mb-1">MOP (kg/ha)</label>
                  <input
                    type="number"
                    value={overrideMop}
                    onChange={(e) => setOverrideMop(parseFloat(e.target.value) || 0)}
                    className="input-clean"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button onClick={handleAgronomistOverride} className="btn-primary">
                  Authorize &amp; Apply Expert Override
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
