"use client";

import React, { useState, useEffect, startTransition, Suspense } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { simulateCrop } from "@/simulation/simulationEngine";
import { CROPS } from "@/simulation/cropConfigs";
import { CropVisualState } from "@/simulation/types";
import { whatIf as apiWhatIf, getTwin } from "@/lib/api";
import Link from "next/link";
import { useFieldParam } from "@/lib/useFieldParam";
import FieldOnboarding from "@/components/ui/FieldOnboarding";

// ─── Sub-components ────────────────────────────────────────────────────────────

// Parses a backend-formatted fertilizer string like "253.5 DAP_kg_ha, 77.6
// UREA_kg_ha" into named quantities — never invents products, only reads the
// real optimizer/ledger output the API already returned.
function parseFertilizerString(s: string): { name: string; value: number }[] {
  const matches = [...s.matchAll(/([\d.]+)\s+([A-Za-z_]+?)_?kg_ha/g)];
  return matches.map((m) => ({ name: m[2].replace(/_/g, ' '), value: parseFloat(m[1]) }));
}

function FertilizerComparison({
  original,
  simulated,
}: {
  original: string;
  simulated: string;
}) {
  const orig = parseFertilizerString(original);
  const sim = parseFertilizerString(simulated);
  if (orig.length === 0 && sim.length === 0) {
    // "N/A" from the backend is a real, valid answer — the field's soil
    // already meets the RDF target so NO_FERTILIZER_NEEDED, not missing
    // data. Say so instead of silently rendering nothing, which looked like
    // the comparison had just failed to load.
    if (original === 'N/A' && simulated === 'N/A') {
      return (
        <div className="bg-white rounded-md border border-[#e5e0d8] p-5 text-center">
          <p className="text-xs font-bold uppercase tracking-wide text-gray-700 mb-1">Fertilizer Plan Comparison</p>
          <p className="text-sm text-green-700">No fertilizer needed — soil already meets the target for this crop and stage.</p>
        </div>
      );
    }
    return null;
  }
  const names = Array.from(new Set([...orig.map((o) => o.name), ...sim.map((s) => s.name)]));

  return (
    <div className="bg-white rounded-md border border-[#e5e0d8] p-5">
      <p className="text-xs font-bold uppercase tracking-wide text-gray-700 mb-4">Fertilizer Plan Comparison</p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {names.map((name) => {
          const o = orig.find((x) => x.name === name)?.value ?? 0;
          const s = sim.find((x) => x.name === name)?.value ?? 0;
          const delta = s - o;
          return (
            <div key={name} className="border border-gray-100 rounded-md p-3 text-center">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-gray-500 mb-2">{name}</div>
              <div className="flex items-center justify-center gap-2">
                <div>
                  <div className="text-lg font-bold text-gray-400 line-through decoration-gray-300">{o}</div>
                  <div className="text-[9px] text-gray-400">baseline</div>
                </div>
                <span className="text-gray-300">→</span>
                <div>
                  <div className={`text-3xl font-extrabold ${delta > 0 ? 'text-amber-600' : delta < 0 ? 'text-green-700' : 'text-gray-800'}`}>{s}</div>
                  <div className="text-[9px] text-gray-400">kg/ha</div>
                </div>
              </div>
              {delta !== 0 && (
                <div className={`text-[10px] font-semibold mt-1 ${delta > 0 ? 'text-amber-600' : 'text-green-700'}`}>
                  {delta > 0 ? '+' : ''}{Math.round(delta * 10) / 10} kg/ha
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ResultChip({ label, color }: { label: string; color: "green" | "amber" | "red" | "blue" | "gray" }) {
  const cls = {
    green: "bg-green-100 text-green-700",
    amber: "bg-amber-100 text-amber-700",
    red: "bg-red-100 text-red-700",
    blue: "bg-blue-100 text-blue-700",
    gray: "bg-gray-100 text-gray-700",
  }[color];
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded ${cls}`}>{label}</span>;
}

function SimSlider({
  label,
  value,
  min,
  max,
  step = 1,
  unit = "",
  displayValue,
  onChange,
  disabled = false,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  displayValue?: string;
  onChange?: (v: number) => void;
  disabled?: boolean;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div className={disabled ? "opacity-50 pointer-events-none" : ""}>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs font-medium text-gray-700">{label}</label>
        <span className="text-xs font-medium text-gray-900 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded min-w-[52px] text-center">
          {displayValue ?? `${value}${unit}`}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange?.(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(to right, #0F4D35 ${pct}%, #e2e8f0 ${pct}%)`,
        }}
      />
      <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

function SimSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1.5">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full text-xs font-medium text-gray-800 bg-white border border-gray-200 rounded-md px-3 py-2.5 appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#0F4D35]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`,
          backgroundRepeat: "no-repeat",
          backgroundPosition: "right 10px center",
          paddingRight: "32px",
        }}
      >
        {options.map((o) => (
          <option key={o}>{o}</option>
        ))}
      </select>
    </div>
  );
}

function GrowthStageTimeline({
  stages,
  currentStage,
  stageProgress = 0,
}: {
  stages: string[];
  currentStage: string;
  stageProgress?: number;
}) {
  const currentIdx = stages.indexOf(currentStage);
  const progressPct = Math.max(0, Math.min(1, stageProgress)) * 100;

  return (
    <div className="flex items-start justify-between gap-1 overflow-x-auto pb-1 min-w-0">
      {stages.map((stageName, i) => {
        const isDone = i < currentIdx;
        const isCurrent = i === currentIdx;
        return (
          <div key={stageName} className="flex flex-col items-center flex-1 min-w-0 relative">
            {/* connector line — the segment leaving the CURRENT stage fills
                proportionally to stageProgress, so moving the planting-shift
                slider (or fertilizer/rainfall/irrigation, which shift the
                simulated day) visibly animates even when the crop hasn't
                crossed into the next named stage yet. */}
            {i < stages.length - 1 && (
              <div className="absolute top-3 left-1/2 w-full h-0.5 z-0 bg-gray-200 overflow-hidden">
                <div
                  className="h-full bg-[#0F4D35] transition-all duration-500"
                  style={{ width: i < currentIdx ? "100%" : i === currentIdx ? `${progressPct}%` : "0%" }}
                />
              </div>
            )}
            {/* dot */}
            <div
              className={`relative z-10 w-6 h-6 rounded-full border-2 flex items-center justify-center mb-1.5 transition-all ${
                isCurrent
                  ? "border-[#0F4D35] bg-[#0F4D35] shadow-sm ring-2 ring-[#0F4D35]/20 animate-pulse"
                  : isDone
                  ? "border-[#0F4D35] bg-[#0F4D35]"
                  : "border-gray-300 bg-white"
              }`}
            >
              {isDone && (
                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              {isCurrent && <div className="w-2 h-2 bg-white rounded-full" />}
            </div>
            <span
              className={`text-[9px] font-medium text-center leading-tight ${
                isCurrent ? "text-[#0F4D35] font-semibold" : isDone ? "text-gray-600" : "text-gray-400"
              }`}
            >
              {stageName}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────
// Every entry here must point at a field that is ACTUALLY that crop in the
// backend — every one of REAL-001..008 is Sugarcane (verified against
// GET /fields), so the old mapping sent the Banana/Cotton/Rice tabs to
// mismatched Sugarcane fields: clicking them showed Sugarcane data under a
// Banana/Cotton tab, or (Rice) a crop that has no record in this system at
// all. Rice has no crop_id in the `crops` table — there is nothing real to
// point it at, so it has no tab rather than a fake one.
const CROP_TO_FIELD: Record<string, string> = {
  sugarcane: 'REAL-001',
  banana: 'FARM-de3b356b-1bfa-4806-aada-a1e0aa8944f4',
  cotton: 'FARM-5df3a349-f1b8-4c0d-b362-f6ebe46e10c4',
};

function SimulatorContent({ initialCrop }: { initialCrop: string }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const fieldParam = searchParams.get('field');

  const [activeCropId, setActiveCropId] = useState<string>(
    initialCrop
  );
  // A ?field= that doesn't correspond to one of the 4 demo crop tabs is still
  // the authoritative field to fetch — the crop tabs are a visual convenience,
  // not the source of truth for which field is selected.
  const [fieldOverride, setFieldOverride] = useState<string | null>(fieldParam);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);
  const [realBaseline, setRealBaseline] = useState<number | null>(null);
  const [realCitation, setRealCitation] = useState<string>('');
  const [realFieldInfo, setRealFieldInfo] = useState<{ crop: string; stage: string; } | null>(null);
  const [twinError, setTwinError] = useState<string | null>(null);

  const activeFieldId = fieldOverride || fieldParam || '';

  function selectCrop(cropId: string) {
    setActiveCropId(cropId);
    setFieldOverride(null);
    const nextField = CROP_TO_FIELD[cropId];
    const params = new URLSearchParams(searchParams.toString());
    params.set('field', nextField);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }

  // Fetch the real baseline from backend twin API whenever active field changes
  useEffect(() => {
    getTwin(activeFieldId)
      .then(data => {
        setTwinError(null);
        // Use the gap N as the required target to apply
        const gap = data.currentPlan?.soilGap;
        if (gap?.N != null) {
          // Real recommended N gap to fill — this is the meaningful "baseline" for this field
          setRealBaseline(Math.round(gap.N));
        } else {
          setRealBaseline(null);
        }
        setRealCitation(data.currentPlan?.citation || '');
        setRealFieldInfo({ crop: data.crop, stage: data.growthStage });
      })
      .catch((err) => {
        setTwinError(err instanceof Error ? err.message : 'Could not load field data');
      });
  }, [activeFieldId, activeCropId]);

  // Inputs
  const crop = CROPS[activeCropId];
  const effectiveBaseline = realBaseline ?? crop.baselineFertilizer;
  const [nKgHa, setNKgHa] = useState(crop.baselineFertilizer);
  const [rainfallPct, setRainfallPct] = useState(0);
  const [applicationTiming, setApplicationTiming] = useState<"Early" | "On time" | "Delayed">("On time");
  const [irrigation, setIrrigation] = useState<"Low" | "Normal" | "High">("Normal");
  const [plantingShift, setPlantingShift] = useState(0);

  // Sync slider to real baseline once it arrives from the backend (intentional
  // one-way sync from fetched data into local editable slider state, not a
  // render-derivable value — eslint-plugin-react-hooks flags this pattern by
  // default even when correct).
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (realBaseline !== null) setNKgHa(realBaseline);
  }, [realBaseline]);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Derived state: now fetched from backend with local fallback
  const [result, setResult] = useState<CropVisualState>(() => simulateCrop({
    cropId: activeCropId,
    fertilizer: CROPS[activeCropId].baselineFertilizer,
    rainfallChange: 0,
    irrigation: "Normal",
    applicationTiming: "On time",
    plantingShift: 0,
  }));
  const [isSimulating, setIsSimulating] = useState(false);
  const [planUnavailable, setPlanUnavailable] = useState(false);
  const [planComparison, setPlanComparison] = useState<{ original: string; simulated: string } | null>(null);
  const [scenarioNote, setScenarioNote] = useState<string>('');

  // Two independent things happen on every slider change, and neither
  // fabricates the other's data:
  //  1. The real fertilizer/cost delta comes ONLY from the backend
  //     /what-if pipeline (ledger + optimizer), which only understands
  //     fertilizer_delta_pct and rainfall_mm — irrigation/timing/planting
  //     shift are not modeled there and are never sent to it.
  //  2. The on-screen crop-condition visual (vigor/leaf/water/nutrient
  //     stress, growth stage) is a local, clearly-labelled structural
  //     simulation (`simulateCrop`) that DOES respond to all five inputs —
  //     it was previously wired only as an error fallback, so moving the
  //     irrigation / timing / planting-shift sliders visibly did nothing.
  useEffect(() => {
    const handler = setTimeout(() => {
      setIsSimulating(true);

      // 1. Local visual simulation — always runs, uses every input.
      setResult(simulateCrop({
        cropId: activeCropId,
        fertilizer: nKgHa,
        rainfallChange: rainfallPct,
        irrigation: irrigation as "Low" | "Normal" | "High",
        applicationTiming: applicationTiming as "Early" | "On time" | "Delayed",
        plantingShift,
      }));

      // 2. Real backend plan delta — fertilizer + rainfall only.
      const baseline = effectiveBaseline;
      // A field whose real N gap is already 0 (soil test shows enough N —
      // a genuine "no fertilizer needed" state, not missing data) makes this
      // a division by zero. NaN/Infinity both serialize to JSON `null` via
      // JSON.stringify, so the backend silently got no delta at all and the
      // slider looked completely inert for these fields. Clamp to the
      // schema's actual bounds (WhatIfRequest.fertilizer_delta_pct: -100..500)
      // instead of sending a value that can't survive being sent.
      const deltaPct = baseline > 0
        ? Math.max(-100, Math.min(500, ((nKgHa - baseline) / baseline) * 100))
        : (nKgHa > 0 ? 500 : 0);
      apiWhatIf(activeFieldId, {
        fertilizer_delta_pct: deltaPct,
        rainfall_mm: rainfallPct > 0 ? 60 : (rainfallPct < 0 ? 0 : 20),
      })
        .then((data) => {
          const sim = data.simulated;
          setPlanUnavailable(false);
          setPlanComparison({ original: data.original.fertilizer, simulated: data.simulated.fertilizer });
          // A labelled scenario estimate, not a validated AI yield prediction —
          // never claim model-backed accuracy the backend doesn't have.
          setScenarioNote(`Scenario estimate: ${sim.yieldBand}. Confidence: ${sim.confidence}. ${sim.cost != null ? `Projected cost: ₹${sim.cost}.` : 'Cost not available.'}`);
          setIsSimulating(false);
        })
        .catch((e) => {
          console.error("Backend what-if call failed:", e);
          setPlanUnavailable(true);
          setPlanComparison(null);
          setScenarioNote('');
          setIsSimulating(false);
        });
    }, 400); // 400ms debounce
    return () => clearTimeout(handler);
  }, [activeCropId, activeFieldId, effectiveBaseline, nKgHa, rainfallPct, irrigation, applicationTiming, plantingShift]);

  // Reset inputs when crop changes
  useEffect(() => {
    startTransition(() => {
      setNKgHa(CROPS[activeCropId].baselineFertilizer);
      setRainfallPct(0);
      setApplicationTiming("On time");
      setIrrigation("Normal");
      setPlantingShift(0);
      setIframeKey((k) => k + 1);
    });
  }, [activeCropId]);

  function handleReset() {
    setNKgHa(effectiveBaseline);
    setRainfallPct(0);
    setApplicationTiming("On time");
    setIrrigation("Normal");
    setPlantingShift(0);
  }

  const getStatusColor = (val: string, reverse = false): "green" | "amber" | "red" | "gray" => {
    const isGood = reverse
      ? ["Low", "Healthy", "Excellent"].includes(val)
      : ["Good", "Healthy", "Excellent"].includes(val);
    const isBad = reverse
      ? ["High", "Severe", "High Stress", "Wilted"].includes(val)
      : ["Poor", "Severe", "High Stress", "Wilted"].includes(val);
    
    if (isGood) return "green";
    if (isBad) return "red";
    return "amber";
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7] font-sans">
      {/* ── Page header ── */}
      <div className="bg-white border-b border-[#e5e0d8] px-6 py-5">
        <div className="max-w-[1400px] mx-auto flex items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <p className="text-[10px] font-bold uppercase tracking-widest text-[#0F4D35]">
                What-If Simulator
              </p>
              <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-[9px] rounded font-medium border border-gray-200">
                Interactive visual simulation
              </span>
              {realFieldInfo && (
                <span className="px-2 py-0.5 bg-green-50 text-green-700 text-[9px] rounded font-medium border border-green-200">
                  Live · {realFieldInfo.crop} · {realFieldInfo.stage} · {activeFieldId}
                </span>
              )}
              {twinError && (
                <span className="px-2 py-0.5 bg-red-50 text-red-700 text-[9px] rounded font-medium border border-red-200">
                  ⚠ Could not load field data: {twinError}
                </span>
              )}
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 leading-tight font-serif">
              See how a change can affect your crop.
            </h1>
            <p className="text-sm text-gray-500 mt-1 max-w-2xl">
              Adjust field conditions and observe the simulated crop response before making a decision.
              {realCitation && <span className="block text-[10px] text-gray-400 italic mt-1">Baseline from: {realCitation}</span>}
            </p>
          </div>
        </div>
      </div>

      {/* ── Fertilizer plan comparison — the most visually obvious delta on screen ── */}
      {planComparison && (
        <div className="max-w-[1400px] mx-auto px-4 md:px-6 pt-4">
          <FertilizerComparison original={planComparison.original} simulated={planComparison.simulated} />
        </div>
      )}

      {/* ── Crop selector ── */}
      <div className="bg-[#FDFBF7] px-6 py-4">
        <div className="max-w-[1400px] mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {Object.values(CROPS).filter((c) => CROP_TO_FIELD[c.id]).map((c) => (
              <button
                key={c.id}
                onClick={() => selectCrop(c.id)}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-sm text-sm font-medium border transition-colors whitespace-nowrap ${
                  activeCropId === c.id
                    ? "bg-[#0F4D35] text-white border-[#0F4D35]"
                    : "bg-white text-gray-600 border-gray-200 hover:border-[#0F4D35]/40 hover:text-[#0F4D35]"
                }`}
              >
                <span className="text-base">{c.icon}</span>
                {c.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Main 3-column layout ── */}
      <div className="max-w-[1400px] mx-auto px-4 md:px-6 pb-12 grid grid-cols-1 lg:grid-cols-[300px_1fr_320px] gap-6">

        {/* ── LEFT: Simulation Inputs ── */}
        <aside className="flex flex-col gap-4">
          <div className="bg-white rounded-md border border-[#e5e0d8] p-5">
            <div className="flex items-center justify-between mb-6">
              <span className="font-semibold text-gray-800 text-sm">Simulation Inputs</span>
              <button
                onClick={handleReset}
                className="flex items-center gap-1 text-[11px] font-medium text-gray-500 hover:text-[#0F4D35] transition-colors"
              >
                Reset
              </button>
            </div>

            <div className="space-y-6">
              <SimSlider
                label="Fertilizer (Nitrogen)"
                value={nKgHa}
                min={0}
                max={150}
                step={5}
                displayValue={`${nKgHa} kg/ha`}
                onChange={setNKgHa}
              />
              <SimSlider
                label="Expected Rainfall Change"
                value={rainfallPct}
                min={-50}
                max={50}
                step={5}
                displayValue={`${rainfallPct > 0 ? "+" : ""}${rainfallPct} %`}
                onChange={setRainfallPct}
              />
              <SimSelect
                label="Irrigation"
                value={irrigation}
                options={["Low", "Normal", "High"]}
                onChange={(v) => setIrrigation(v as "Low" | "Normal" | "High")}
              />
              <SimSelect
                label="Application Timing"
                value={applicationTiming}
                options={["Early", "On time", "Delayed"]}
                onChange={(v) => setApplicationTiming(v as "Early" | "On time" | "Delayed")}
              />
              <SimSlider
                label="Planting Date Shift"
                value={plantingShift}
                min={-60}
                max={90}
                step={5}
                displayValue={`${plantingShift > 0 ? "+" : ""}${plantingShift} days`}
                onChange={setPlantingShift}
              />
            </div>
          </div>
        </aside>

        {/* ── CENTER: 3D Model viewer + timeline ── */}
        <div className="flex flex-col gap-4 min-w-0">
          <div className="bg-white rounded-md border border-[#e5e0d8] overflow-hidden flex flex-col h-[460px]">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#e5e0d8] bg-gray-50/50">
              <div className="flex items-center gap-2">
                <span className="text-lg">{crop.icon}</span>
                <div>
                  <p className="text-sm font-bold text-gray-900">{crop.name}</p>
                  <p className="text-[10px] text-gray-500 font-medium">3D Growth Simulation</p>
                </div>
              </div>
              {crop.has3D && (
                <button
                  onClick={() => setIsFullscreen(true)}
                  className="text-xs font-medium text-gray-600 hover:text-[#0F4D35] px-2 py-1 transition-colors"
                >
                  Fullscreen
                </button>
              )}
            </div>

            <div className="relative flex-1 bg-gradient-to-b from-gray-50 to-gray-100/50">
              {crop.has3D ? (
                <iframe
                  key={iframeKey}
                  title={crop.sketchfabTitle}
                  className="w-full h-full"
                  frameBorder="0"
                  allowFullScreen
                  allow="autoplay; fullscreen; xr-spatial-tracking"
                  src={`https://sketchfab.com/models/${crop.sketchfabId}/embed?autostart=1&ui_watermark=0&ui_infos=0&ui_stop=0`}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <p className="text-sm text-gray-400">3D Model unavailable. Using structural representation.</p>
                </div>
              )}
              
              {/* Subtle status overlay showing connection status */}
              <div className="absolute top-3 left-3 bg-white/80 backdrop-blur-sm border border-white/50 px-2 py-1 rounded text-[9px] text-gray-500 font-medium">
                Simulation state · Model connection pending
              </div>
            </div>
          </div>

          <div className="bg-white rounded-md border border-[#e5e0d8] p-5">
            <p className="text-xs font-semibold text-gray-500 mb-4 uppercase tracking-wide">
              Growth Stage Timeline
            </p>
            <GrowthStageTimeline stages={crop.stages} currentStage={result.stage} stageProgress={result.stageProgress} />
          </div>
        </div>

        {/* ── RIGHT: Simulation Results ── */}
        <aside className="flex flex-col gap-4">
          <div className="bg-white rounded-md border border-[#e5e0d8] p-5 flex flex-col gap-5">
            <div className="flex items-center gap-2 mb-1 border-b border-[#e5e0d8] pb-3">
              <span className="font-bold text-gray-800 text-sm">Crop Condition</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider mb-1">Current Stage</p>
                <p className="text-sm font-semibold text-gray-900">{result.stage}</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider mb-1">Stage Progress</p>
                <p className="text-sm font-semibold text-gray-900">{Math.round(result.stageProgress * 100)}%</p>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              {[
                { label: "Plant Vigor", val: result.vigor, rev: false },
                { label: "Leaf Condition", val: result.leafCondition, rev: false },
                { label: "Water Stress", val: result.waterStress, rev: true },
                { label: "Nutrient Stress", val: result.nutrientStress, rev: true },
              ].map(({ label, val, rev }) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="text-xs text-gray-600 font-medium">{label}</span>
                  <ResultChip label={val} color={getStatusColor(val, rev)} />
                </div>
              ))}
            </div>
            
            <div className="mt-2 pt-4 border-t border-[#e5e0d8]">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-800 font-bold">Overall Visual State</span>
                  <ResultChip label={result.overallState} color={getStatusColor(result.overallState, true)} />
                </div>
            </div>
          </div>

          <div className="bg-white rounded-md border border-[#e5e0d8] p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-bold text-gray-800">What changed?</p>
              {planUnavailable && (
                <span className="text-[9px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded-full">
                  Real plan unavailable — visual only
                </span>
              )}
            </div>
            <p className="text-[13px] text-gray-600 leading-relaxed mb-2">
              {result.explanation}
            </p>
            {scenarioNote && (
              <p className="text-[13px] text-gray-600 leading-relaxed pt-2 border-t border-[#e5e0d8]">
                {scenarioNote}
              </p>
            )}
          </div>
        </aside>
      </div>

      {/* ── Fullscreen 3D overlay ── */}
      {isFullscreen && crop.has3D && (
        <div className="fixed inset-0 z-[200] bg-[#FDFBF7] flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-[#e5e0d8] bg-white">
            <div className="flex items-center gap-2">
              <span className="text-lg">{crop.icon}</span>
              <span className="text-sm font-bold text-gray-900">{crop.name}</span>
            </div>
            <button
              onClick={() => setIsFullscreen(false)}
              className="text-sm text-gray-600 hover:text-gray-900 font-medium"
            >
              Close
            </button>
          </div>
          <div className="flex-1 w-full bg-gray-50">
            <iframe
              title={crop.sketchfabTitle}
              className="w-full h-full"
              frameBorder="0"
              allowFullScreen
              allow="autoplay; fullscreen; xr-spatial-tracking"
              src={`https://sketchfab.com/models/${crop.sketchfabId}/embed?autostart=1&ui_watermark=0&ui_infos=0&ui_stop=0`}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default function SimulatorPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#FDFBF7] flex items-center justify-center text-sm text-gray-500">Loading…</div>}>
      <SimulatorEntry />
    </Suspense>
  );
}

function SimulatorEntry() {
  const { fieldId, setFieldId, fields, fieldsError } = useFieldParam();
  if (!fieldId) return <FieldOnboarding fields={fields} fieldsError={fieldsError} onSelect={setFieldId} />;
  return <SimulatorGate key={fieldId} fieldId={fieldId} />;
}

function SimulatorGate({ fieldId }: { fieldId: string }) {
  const [state, setState] = useState<{ crop: string; ready: boolean } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    getTwin(fieldId, controller.signal).then(twin => {
      // twin.crop is the backend's display name (e.g. "Cotton (Bt)"), not a
      // clean code — strip any "(...)" suffix before matching it against
      // the local CROPS config keys (rice/banana/cotton/sugarcane), or every
      // crop whose display name isn't already lowercase-identical to its
      // key (Cotton, in practice) would wrongly show "Simulation unavailable".
      const cleanCrop = twin.crop.split('(')[0].trim().toLowerCase();
      if (!controller.signal.aborted) setState({ crop: cleanCrop, ready: twin.hasSoilTest && !['NO_DATA', 'ABSTAIN'].includes(twin.currentPlan.status) });
    }).catch(err => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Could not load your field.'); });
    return () => controller.abort();
  }, [fieldId]);
  if (state?.ready && CROPS[state.crop]) return <SimulatorContent initialCrop={state.crop} />;
  return <main className="min-h-screen bg-gray-50 p-10 text-center">
    <h1 className="text-xl font-bold">{error ? 'Field unavailable' : !state ? 'Loading your field…' : state.ready ? 'Simulation unavailable for this crop' : 'Complete your field first'}</h1>
    <p className="my-4 text-gray-600">{error || 'The simulator needs confirmed soil data and a recommendation for your selected field.'}</p>
    <Link className="text-green-800 underline" href={`/dashboard?field=${encodeURIComponent(fieldId)}`}>Continue to your field</Link>
  </main>;
}
