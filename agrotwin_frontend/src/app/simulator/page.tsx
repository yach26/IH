"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { getAuthHeaders } from "@/lib/auth";
import SimulationTimeline, { TimelineStage } from "@/components/features/SimulationTimeline";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FieldSummary {
  id: number;
  code: string;
  crop?: string;
}

interface WhatIfResult {
  original_plan?: { what?: string; how_much?: Record<string, number>; when?: string };
  simulated_plan?: { what?: string; how_much?: Record<string, number>; when?: string; status?: string };
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

function SimulatorContent() {
  const searchParams = useSearchParams();
  const [selectedFieldId, setSelectedFieldId] = useState<string>(searchParams.get("field") || "1");
  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [whatIfFertDelta, setWhatIfFertDelta] = useState(0);
  const [whatIfRainfall, setWhatIfRainfall] = useState(0);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResult | null>(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [simDay, setSimDay] = useState(0);
  const [activeCrop, setActiveCrop] = useState("SUGARCANE");

  const loadFields = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/fields`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setFields(data.fields || []);
        const first = data.fields?.[0];
        if (first?.crop) setActiveCrop(first.crop);
      }
    } catch (e) {
      console.error("Failed to load fields", e);
    }
  }, []);

  useEffect(() => {
    loadFields();
  }, [loadFields]);

  const handleFieldChange = (fieldId: string) => {
    setSelectedFieldId(fieldId);
    const field = fields.find((f) => f.id === parseInt(fieldId));
    if (field?.crop) setActiveCrop(field.crop);
    setWhatIfResult(null);
    setSimDay(0);
  };

  const handleRunWhatIf = async () => {
    setWhatIfLoading(true);
    try {
      const res = await fetch(`${API_BASE}/fields/${selectedFieldId}/what-if`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({
          fertilizer_delta_pct: whatIfFertDelta,
          rainfall_mm: whatIfRainfall,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setWhatIfResult(data);
      }
    } catch (e) {
      console.error("What-if failed", e);
    } finally {
      setWhatIfLoading(false);
    }
  };

  const stages = getStagesForCrop(activeCrop);
  const totalDuration = STAGE_DURATIONS[activeCrop] || 180;
  const currentStageIndex = stages.findIndex((s) => simDay >= s.dayStart && simDay < s.dayEnd);

  return (
    <div className="min-h-screen bg-bg-light">
      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-ink-primary">What-If Simulator</h1>
            <p className="text-sm text-ink-secondary mt-1">
              Simulate variations without modifying saved farm data
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

        {/* Simulation Timeline */}
        <div className="card-clean">
          <h3 className="text-base font-bold text-ink-primary mb-4">Growth Stage Projection</h3>
          <SimulationTimeline
            stages={stages}
            currentStageIndex={currentStageIndex >= 0 ? currentStageIndex : 0}
            currentDay={simDay}
            totalDuration={totalDuration}
            onSeek={setSimDay}
            label="Simulated Growth Timeline"
          />
          <p className="text-xs text-ink-muted mt-3">Illustrative projection based on current data</p>
        </div>

        {/* Controls */}
        <div className="card-clean">
          <h3 className="text-base font-bold text-ink-primary mb-4">Simulation Controls</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-4">
            <div>
              <label className="text-sm font-semibold text-ink-primary block mb-2">
                Fertilizer Rate: {whatIfFertDelta > 0 ? `+${whatIfFertDelta}` : whatIfFertDelta}%
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
                <span>-50%</span>
                <span>0%</span>
                <span>+50%</span>
              </div>
            </div>
            <div>
              <label className="text-sm font-semibold text-ink-primary block mb-2">
                Rainfall (7d): {whatIfRainfall} mm
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
                <span>0 mm</span>
                <span>60 mm</span>
                <span>120 mm</span>
              </div>
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <button onClick={handleRunWhatIf} disabled={whatIfLoading} className="btn-primary">
              {whatIfLoading ? "Running..." : "Run What-If Analysis"}
            </button>
          </div>
        </div>

        {/* Results */}
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
      </main>
    </div>
  );
}

export default function SimulatorPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm text-ink-secondary">Loading...</p>
        </div>
      </div>
    }>
      <SimulatorContent />
    </Suspense>
  );
}
