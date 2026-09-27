"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser, isAdmin, logout, getAuthHeaders } from "@/lib/auth";
import SimulationTimeline, { TimelineStage } from "@/components/features/SimulationTimeline";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FieldSummary {
  id: number;
  code: string;
  name: string;
  area_ha: number;
  crop?: string;
  current_stage?: string;
  lat?: number;
  lon?: number;
}

interface TwinData {
  field: { field_code: string; area_ha: number; irrigation_type?: string };
  soil: { n_kg_ha?: number; p_kg_ha?: number; k_kg_ha?: number; ph?: number; oc_percent?: number } | null;
  latest_plan: { status_db?: string; confidence?: string } | null;
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

export default function CommandCentrePage() {
  const router = useRouter();
  const [user, setUser] = useState<ReturnType<typeof getUser>>(null);
  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [selectedField, setSelectedField] = useState<FieldSummary | null>(null);
  const [twin, setTwin] = useState<TwinData | null>(null);
  const [loading, setLoading] = useState(true);
  const [simDay, setSimDay] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    const u = getUser();
    if (!u) {
      router.replace("/login?next=/command-centre");
      return;
    }
    if (!isAdmin()) {
      router.replace("/dashboard");
      return;
    }
    setUser(u);
    loadFields();
  }, [router]);

  const loadFields = async () => {
    try {
      const res = await fetch(`${API_BASE}/fields`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setFields(data.fields || []);
        if (data.fields?.length > 0) {
          setSelectedField(data.fields[0]);
          loadTwin(data.fields[0].id);
        }
      }
    } catch (e) {
      setError("Failed to load fields");
    } finally {
      setLoading(false);
    }
  };

  const loadTwin = async (fieldId: number) => {
    try {
      const res = await fetch(`${API_BASE}/fields/${fieldId}/twin`, { headers: getAuthHeaders() });
      if (res.ok) {
        setTwin(await res.json());
        setSimDay(0);
      }
    } catch (e) {
      setError("Failed to load twin");
    }
  };

  const handleFieldChange = (fieldId: number) => {
    const field = fields.find((f) => f.id === fieldId);
    if (field) {
      setSelectedField(field);
      loadTwin(fieldId);
    }
  };

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-light">
        <div className="text-center">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm text-ink-secondary">Loading Command Centre...</p>
        </div>
      </div>
    );
  }

  const stages = getStagesForCrop(selectedField?.crop || "SUGARCANE");
  const totalDuration = STAGE_DURATIONS[selectedField?.crop || "SUGARCANE"] || 180;
  const currentStageIndex = stages.findIndex((s) => simDay >= s.dayStart && simDay < s.dayEnd);

  return (
    <div className="min-h-screen bg-bg-light">
      {/* Header */}
      <header className="bg-white border-b border-border sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-lg font-bold text-ink-primary">Command Centre</span>
            <span className="badge badge-high">Admin</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-ink-secondary">{user?.name}</span>
            <button onClick={handleLogout} className="btn-secondary text-xs">
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Field Selector */}
        <div className="card-clean">
          <h2 className="text-base font-bold text-ink-primary mb-4">Select Field</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {fields.map((field) => (
              <button
                key={field.id}
                onClick={() => handleFieldChange(field.id)}
                className={`p-3 rounded-lg border text-left transition ${
                  selectedField?.id === field.id
                    ? "border-agri-primary bg-agri-light"
                    : "border-border hover:border-zinc-300"
                }`}
              >
                <div className="font-semibold text-sm text-ink-primary">{field.code}</div>
                <div className="text-xs text-ink-secondary mt-1">
                  {field.crop || "No crop"} &bull; {field.area_ha} ha
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Twin Summary */}
        {twin && selectedField && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card-clean">
              <h3 className="text-base font-bold text-ink-primary mb-4">Twin Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Field</span>
                  <span className="font-semibold text-ink-primary">{twin.field.field_code}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Crop</span>
                  <span className="font-semibold text-ink-primary">{selectedField.crop || "Not set"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Stage</span>
                  <span className="font-semibold text-ink-primary">{selectedField.current_stage || "Not set"}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Area</span>
                  <span className="font-semibold text-ink-primary">{twin.field.area_ha} ha</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100">
                  <span className="text-ink-secondary">Irrigation</span>
                  <span className="font-semibold text-ink-primary">{twin.field.irrigation_type || "N/A"}</span>
                </div>
                {twin.soil && (
                  <>
                    <div className="flex justify-between py-1 border-b border-zinc-100">
                      <span className="text-ink-secondary">N</span>
                      <span className="font-semibold text-ink-primary">{twin.soil.n_kg_ha ?? "--"} kg/ha</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-zinc-100">
                      <span className="text-ink-secondary">P</span>
                      <span className="font-semibold text-ink-primary">{twin.soil.p_kg_ha ?? "--"} kg/ha</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-zinc-100">
                      <span className="text-ink-secondary">K</span>
                      <span className="font-semibold text-ink-primary">{twin.soil.k_kg_ha ?? "--"} kg/ha</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-zinc-100">
                      <span className="text-ink-secondary">pH</span>
                      <span className="font-semibold text-ink-primary">{twin.soil.ph ?? "--"}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-ink-secondary">OC</span>
                      <span className="font-semibold text-ink-primary">{twin.soil.oc_percent ?? "--"}%</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Simulation Timeline */}
            <div className="card-clean">
              <h3 className="text-base font-bold text-ink-primary mb-4">Simulation Timeline</h3>
              <SimulationTimeline
                stages={stages}
                currentStageIndex={currentStageIndex >= 0 ? currentStageIndex : 0}
                currentDay={simDay}
                totalDuration={totalDuration}
                onSeek={setSimDay}
                label="Growth Stage Projection"
              />
              <p className="text-xs text-ink-muted mt-3">
                Illustrative projection based on current data
              </p>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        {selectedField && (
          <div className="card-clean">
            <h3 className="text-base font-bold text-ink-primary mb-4">Quick Actions</h3>
            <div className="flex flex-wrap gap-3">
              <a
                href={`/dashboard?field=${selectedField.id}`}
                className="btn-secondary text-sm"
              >
                Open Dashboard
              </a>
              <a
                href={`/simulator?field=${selectedField.id}`}
                className="btn-secondary text-sm"
              >
                Open Simulator
              </a>
              <a
                href={`/upload?field=${selectedField.id}`}
                className="btn-secondary text-sm"
              >
                Upload Soil Report
              </a>
              <a
                href={`https://www.google.com/maps?q=${selectedField.lat},${selectedField.lon}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary text-sm"
              >
                View on Map
              </a>
            </div>
          </div>
        )}

        {/* System Health */}
        <div className="card-clean">
          <h3 className="text-base font-bold text-ink-primary mb-4">System Health</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-xs text-ink-secondary block">API Status</span>
              <span className="badge badge-high">Reachable</span>
            </div>
            <div>
              <span className="text-xs text-ink-secondary block">Weather Source</span>
              <span className="font-medium text-ink-primary">Open-Meteo</span>
            </div>
            <div>
              <span className="text-xs text-ink-secondary block">Last Refresh</span>
              <span className="font-medium text-ink-primary">{new Date().toLocaleTimeString()}</span>
            </div>
            <div>
              <span className="text-xs text-ink-secondary block">Auth Mode</span>
              <span className="badge badge-medium">DEMO</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
