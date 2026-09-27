"use client";

import React, { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getAuthHeaders } from "@/lib/auth";
import SimulationTimeline, { TimelineStage } from "@/components/features/SimulationTimeline";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FieldMeta {
  field_id: number;
  field_code: string;
  area_ha: number;
  irrigation_type?: string;
  current_stage?: string;
  sowing_date?: string;
  recommendation_type?: string;
  lat?: number;
  lon?: number;
}

interface SoilData {
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
  confidence?: string;
  flags?: string[];
  status_db?: string;
  based_on?: { citation?: string; cost_estimate?: number };
}

interface FarmAlert {
  alert_type?: string;
  severity?: string;
  message?: string;
}

interface FieldSummary {
  id: number;
  code: string;
  crop?: string;
  area_ha: number;
  lat?: number;
  lon?: number;
}

const STAGE_DURATIONS: Record<string, number> = {
  BANANA: 365,
  SUGARCANE: 365,
  COTTON: 180,
  SOYBEAN: 120,
};

const STAGE_LABELS = ["Germination", "Vegetative", "Flowering", "Fruiting", "Maturity"];

function getStagesForCrop(crop: string): TimelineStage[] {
  const duration = STAGE_DURATIONS[crop] || 180;
  const stageCount = STAGE_LABELS.length;
  const stageDuration = Math.floor(duration / stageCount);
  return STAGE_LABELS.map((label, i) => ({
    id: `stage-${i}`,
    label,
    dayStart: i * stageDuration,
    dayEnd: (i + 1) * stageDuration,
  }));
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [selectedFieldId, setSelectedFieldId] = useState<string>(
    searchParams.get("field") || "1"
  );
  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [fieldData, setFieldData] = useState<FieldMeta | null>(null);
  const [soilData, setSoilData] = useState<SoilData | null>(null);
  const [latestPlan, setLatestPlan] = useState<RecommendationPlan | null>(null);
  const [alerts, setAlerts] = useState<FarmAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [showProof, setShowProof] = useState(false);
  const [selectedOptimizer, setSelectedOptimizer] = useState("heuristic");
  const [simDay, setSimDay] = useState(0);
  const activeFetch = useRef<AbortController | null>(null);

  const fetchTwinData = useCallback(async (fId: string) => {
    activeFetch.current?.abort();
    const controller = new AbortController();
    activeFetch.current = controller;
    const { signal } = controller;
    setLoading(true);
    setActionMessage(null);
    try {
      const res = await fetch(`${API_BASE}/fields/${fId}/twin`, { signal, headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setFieldData(data.field);
        setSoilData(data.soil);
        setLatestPlan(data.latest_plan);
      }
      const alertRes = await fetch(`${API_BASE}/fields/${fId}/alerts`, { signal, headers: getAuthHeaders() });
      if (alertRes.ok) {
        const aData = await alertRes.json();
        setAlerts(aData.alerts || []);
      }
    } catch (e: unknown) {
      if (!signal.aborted) setActionMessage(`Error loading twin: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      if (!signal.aborted) setLoading(false);
    }
  }, []);

  const loadFields = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/fields`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setFields(data.fields || []);
      }
    } catch (e) {
      console.error("Failed to load fields", e);
    }
  }, []);

  useEffect(() => {
    loadFields();
  }, [loadFields]);

  useEffect(() => {
    if (selectedFieldId) {
      fetchTwinData(selectedFieldId);
    }
  }, [selectedFieldId, fetchTwinData]);

  const handleFieldChange = (fieldId: string) => {
    setSelectedFieldId(fieldId);
    setSimDay(0);
    router.replace(`/dashboard?field=${fieldId}`);
  };

  const handleRecommend = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ optimizer: selectedOptimizer }),
      });
      if (res.ok) {
        const plan = await res.json();
        setLatestPlan(plan);
        setActionMessage("Recommendation generated successfully!");
        fetchTwinData(selectedFieldId);
      }
    } catch (e) {
      setActionMessage(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerHeavyRain = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({
          type: "HEAVY_RAIN_ALERT",
          field_id: parseInt(selectedFieldId),
          payload: { heavy_rain_alert: true, rainfall_probability: 95, rainfall_mm_next_7d: 85.0 },
        }),
      });
      if (res.ok) {
        setActionMessage("HEAVY_RAIN_ALERT injected! Plan invalidated and rescheduled.");
        fetchTwinData(selectedFieldId);
      }
    } catch (e) {
      setActionMessage(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  const scrollToMap = () => {
    const el = document.getElementById("field-map");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  const stages = getStagesForCrop(fieldData?.recommendation_type || "SUGARCANE");
  const totalDuration = STAGE_DURATIONS[fieldData?.recommendation_type || "SUGARCANE"] || 180;
  const currentStageIndex = stages.findIndex((s) => simDay >= s.dayStart && simDay < s.dayEnd);

  if (loading && !fieldData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm text-ink-secondary">Loading Digital Twin...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Field Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-primary">Digital Twin Dashboard</h1>
          <p className="text-sm text-ink-secondary mt-1">
            Field {fieldData?.field_code || selectedFieldId} &bull; {fieldData?.area_ha || "--"} ha
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label htmlFor="field-select" className="text-sm font-medium text-ink-secondary">Field:</label>
          <select
            id="field-select"
            value={selectedFieldId}
            onChange={(e) => handleFieldChange(e.target.value)}
            className="input-clean font-medium max-w-[240px]"
          >
            {fields.map((f) => (
              <option key={f.id} value={f.id}>
                {f.code} {f.crop ? `(${f.crop})` : ""}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Status Banner */}
      {actionMessage && (
        <div className="p-4 rounded-lg bg-agri-light text-agri-primary border border-agri-primary/20 text-sm font-medium flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-agri-primary hover:text-agri-hover font-bold ml-4">&times;</button>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="p-4 rounded-xl border border-amber-300 bg-amber-50">
          <div className="flex items-center gap-2 text-amber-800 font-semibold text-sm">
            <span>&#9888; Active Alerts ({alerts.length})</span>
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

      {/* Recommendation Card */}
      <div className="card-clean border-2 border-agri-primary/30">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-border gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">Current Active Plan</span>
            <h2 className="text-2xl font-bold text-ink-primary mt-1">
              {latestPlan?.what || "No Application Scheduled"}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <span className={`badge ${
              latestPlan?.confidence === "HIGH" ? "badge-high" :
              latestPlan?.confidence === "MEDIUM" ? "badge-medium" :
              latestPlan?.confidence === "LOW" ? "badge-low" : "badge-abstain"
            }`}>
              {latestPlan?.confidence || "UNKNOWN"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-6 border-b border-border">
          <div>
            <span className="text-xs font-medium text-ink-secondary">Nutrient Requirements</span>
            <div className="mt-2 space-y-2">
              {latestPlan?.how_much && Object.keys(latestPlan.how_much).length > 0 ? (
                Object.entries(latestPlan.how_much).map(([k, v]) => (
                  <div key={k} className="flex justify-between items-center text-sm py-1 border-b border-zinc-100">
                    <span className="font-medium text-ink-primary">{k.replace("_kg_ha", "")}</span>
                    <span className="font-semibold text-agri-primary">{v} kg/ha</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-ink-muted">No nutrient deficit.</p>
              )}
            </div>
          </div>
          <div>
            <span className="text-xs font-medium text-ink-secondary">Application Window</span>
            <p className="text-sm font-semibold text-ink-primary mt-2">{latestPlan?.when || "Pending"}</p>
          </div>
          <div>
            <span className="text-xs font-medium text-ink-secondary">Estimated Investment</span>
            <p className="text-xl font-bold text-ink-primary mt-2">
              {latestPlan?.based_on?.cost_estimate ? `₹${latestPlan.based_on.cost_estimate.toLocaleString()}` : "₹0"}
            </p>
          </div>
        </div>

        <div className="pt-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button onClick={() => setShowProof(!showProof)} className="btn-secondary">
              {showProof ? "Hide Evidence" : "Why This Plan?"}
            </button>
            <button onClick={scrollToMap} className="btn-secondary">View on Map</button>
            <a
              href={`https://www.google.com/maps?q=${fieldData?.lat},${fieldData?.lon}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-xs"
            >
              Open in Google Maps
            </a>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedOptimizer}
              onChange={(e) => setSelectedOptimizer(e.target.value)}
              className="input-clean text-xs py-1.5 px-2 max-w-[170px]"
            >
              <option value="heuristic">Heuristic</option>
              <option value="linprog">Linprog (LP)</option>
            </select>
            <button onClick={handleRecommend} className="btn-primary">Re-evaluate Plan</button>
            <button onClick={handleTriggerHeavyRain} className="bg-amber-600 hover:bg-amber-700 text-white px-3 py-2 rounded-lg text-xs font-medium transition">
              &#9748; Test Heavy Rain
            </button>
          </div>
        </div>

        {showProof && (
          <div className="mt-6 pt-6 border-t border-border">
            <h3 className="text-base font-bold text-ink-primary mb-3">Proof-Carrying Recommendation</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-3 rounded-lg bg-bg-subtle">
                <strong className="text-ink-primary block">WHAT & HOW MUCH:</strong>
                <p className="text-ink-secondary">{latestPlan?.what} — {JSON.stringify(latestPlan?.how_much || {})}</p>
              </div>
              <div className="p-3 rounded-lg bg-bg-subtle">
                <strong className="text-ink-primary block">WHEN:</strong>
                <p className="text-ink-secondary">{latestPlan?.when}</p>
              </div>
              <div className="p-3 rounded-lg bg-bg-subtle">
                <strong className="text-ink-primary block">WHY:</strong>
                <p className="text-ink-secondary">Based on soil test + crop RDF</p>
              </div>
              <div className="p-3 rounded-lg bg-bg-subtle">
                <strong className="text-ink-primary block">HOW SURE:</strong>
                <p className="text-ink-secondary">Confidence: {latestPlan?.confidence} | Flags: {latestPlan?.flags?.join(", ") || "None"}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Simulation Timeline */}
      <div className="card-clean">
        <h3 className="text-base font-bold text-ink-primary mb-4">Crop Stage Timeline</h3>
        <SimulationTimeline
          stages={stages}
          currentStageIndex={currentStageIndex >= 0 ? currentStageIndex : 0}
          currentDay={simDay}
          totalDuration={totalDuration}
          onSeek={setSimDay}
          label="Growth Stage Projection"
        />
        <p className="text-xs text-ink-muted mt-3">Illustrative projection based on current data</p>
      </div>

      {/* Soil + Crop State */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card-clean">
          <h3 className="text-base font-bold text-ink-primary mb-4">Active Crop State</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-1 border-b border-zinc-100">
              <span className="text-ink-secondary">Crop</span>
              <span className="font-semibold text-ink-primary">{fieldData?.recommendation_type || "Not set"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-zinc-100">
              <span className="text-ink-secondary">Growth Stage</span>
              <span className="font-semibold text-ink-primary">{fieldData?.current_stage || "Not set"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-zinc-100">
              <span className="text-ink-secondary">Sowing Date</span>
              <span className="font-semibold text-ink-primary">{fieldData?.sowing_date || "N/A"}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-ink-secondary">Irrigation</span>
              <span className="font-semibold text-ink-primary">{fieldData?.irrigation_type || "N/A"}</span>
            </div>
          </div>
        </div>

        <div className="card-clean">
          <h3 className="text-base font-bold text-ink-primary mb-4">Soil Test Metrics</h3>
          <div className="space-y-4">
            {[
              { label: "Nitrogen (N)", value: soilData?.n_kg_ha, max: 250, unit: "kg/ha" },
              { label: "Phosphorus (P)", value: soilData?.p_kg_ha, max: 60, unit: "kg/ha" },
              { label: "Potassium (K)", value: soilData?.k_kg_ha, max: 450, unit: "kg/ha" },
            ].map(({ label, value, max, unit }) => (
              <div key={label}>
                <div className="flex justify-between text-xs font-medium mb-1">
                  <span>{label}</span>
                  <span className="font-bold">{value ?? "--"} {unit}</span>
                </div>
                <div className="w-full bg-zinc-100 rounded-full h-2">
                  <div
                    className="bg-agri-primary h-2 rounded-full"
                    style={{ width: `${Math.min(100, ((value || 0) / max) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-zinc-100 text-xs text-ink-secondary">
              <div>pH: <strong className="text-ink-primary">{soilData?.ph ?? "--"}</strong></div>
              <div>OC: <strong className="text-ink-primary">{soilData?.oc_percent ?? "--"}%</strong></div>
            </div>
          </div>
        </div>
      </div>

      {/* Field Map */}
      <div id="field-map" className="card-clean">
        <h3 className="text-base font-bold text-ink-primary mb-4">Field Location</h3>
        <div className="bg-zinc-100 rounded-lg h-48 flex items-center justify-center">
          <div className="text-center">
            <p className="text-sm text-ink-secondary">
              {fieldData?.lat && fieldData?.lon
                ? `${fieldData.lat.toFixed(4)}, ${fieldData.lon.toFixed(4)}`
                : "Location not available"}
            </p>
            {fieldData?.lat && fieldData?.lon && (
              <a
                href={`https://www.google.com/maps?q=${fieldData.lat},${fieldData.lon}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary text-xs mt-2 inline-block"
              >
                Open in Google Maps
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm text-ink-secondary">Loading...</p>
        </div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
