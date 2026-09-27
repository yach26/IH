"use client";

import React, { Suspense } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { getTwin, recommend, ApiError, type TwinResponse } from '@/lib/api';
import { useFieldParam } from '@/lib/useFieldParam';
import FieldSelector from '@/components/ui/FieldSelector';
import FieldOnboarding from '@/components/ui/FieldOnboarding';
import StageTimeline from '@/components/ui/StageTimeline';

const FieldMap = dynamic(() => import('@/components/ui/FieldMap'), { ssr: false });

// ─── Helpers ──────────────────────────────────────────────────────────────────
function confidenceBadgeClass(confidence: string): string {
  const level = confidence.toUpperCase();
  if (level === 'HIGH') return 'bg-green-50 text-green-700 border-green-200';
  if (level === 'MEDIUM') return 'bg-amber-50 text-amber-700 border-amber-200';
  if (level === 'LOW') return 'bg-orange-50 text-orange-700 border-orange-200';
  if (level === 'ABSTAIN') return 'bg-red-50 text-red-700 border-red-200';
  return 'bg-blue-50 text-blue-600 border-blue-200';
}

function nutrientLabel(score: number | null): string {
  if (score == null) return 'Not available';
  if (score >= 80) return 'High';
  if (score >= 45) return 'Moderate';
  return 'Low';
}

function StatusDot({ color }: { color: string }) {
  const map: Record<string, string> = {
    'text-green-500': 'bg-green-500',
    'text-amber-500': 'bg-amber-500',
    'text-gray-400': 'bg-gray-300',
    'text-red-500': 'bg-red-500',
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${map[color] || 'bg-gray-400'}`} />;
}

// ─── Types ────────────────────────────────────────────────────────────────────
type NutrientEntry = { value: number | null; score: number | null; label: string; color: string };
type FieldState = {
  id: string;
  status: string;
  location: string | null;
  crop: string;
  stage: string;
  stageSequence: string[];
  area: string;
  soilType: string | null;
  lat: number | null;
  lon: number | null;
  hasSoilTest: boolean;
  soilHealthScore: number | null;
  weather: { available: boolean; rainfall7d: number | null; heavy_rain_alert: boolean; condition: string | null };
  soil: {
    n: NutrientEntry;
    p: NutrientEntry;
    k: NutrientEntry;
    ph: number | null;
    oc: number | null;
    note: string;
  };
  fieldStatus: {
    cropCondition: { label: string; color: string };
    waterStress: { label: string; color: string };
    overall: string;
  };
  recommendation: {
    action: string;
    window: string;
    description: string;
    quantity: string;
    applicationWindow: string;
    estimatedCost: number | null;
    costCitation: string | null;
    confidence: string;
    citation: string;
    status: string;
    reason: string | null;
    requiredActions: string[];
    flags: string[];
  };
  timeline: string[];
  activeAlert: { title: string; description: string } | null;
};

function mapTwinToFieldState(data: TwinResponse): FieldState {
  const nutrients = data.nutrients || {};
  const soil = data.soilDetail || {};
  const plan = data.currentPlan || ({} as TwinResponse['currentPlan']);
  const weather = data.weather || { available: false, rainfall_mm_next_7d: null, heavy_rain_alert: false, condition: null };
  const stages: string[] = data.stageSequence || [];
  const currentStageName = data.growthStage || '';

  const nScore = soil.n_score ?? null;
  const kScore = soil.k_score ?? null;

  // Water stress and crop condition only have a real signal when the
  // relevant backend data actually exists — otherwise "not available", never
  // a fabricated "Good"/"Low".
  const weatherKnown = weather.available;
  const rainfallOk = weatherKnown ? !weather.heavy_rain_alert : null;
  const waterStress = rainfallOk == null ? 'Not available' : rainfallOk ? 'Low' : 'High';
  const waterColor = rainfallOk == null ? 'text-gray-400' : rainfallOk ? 'text-gray-400' : 'text-red-500';
  const nSufficient = nScore != null ? nScore >= 60 : null;
  const cropCond = nSufficient == null ? 'Not available' : nSufficient ? 'Good' : 'Moderate';
  const cropColor = nSufficient == null ? 'text-gray-400' : nSufficient ? 'text-green-500' : 'text-amber-500';
  const overall = (nSufficient && rainfallOk) ? 'Healthy' : (nSufficient == null && rainfallOk == null) ? 'Unknown' : 'Needs Attention';

  const gap = plan.soilGap || {};
  const description = `Based on real soil test (N=${nutrients.n?.current ?? '—'} kg/ha, P=${nutrients.p?.current ?? '—'} kg/ha, K=${nutrients.k?.current ?? '—'} kg/ha) and ${data.crop} at ${currentStageName} stage. Nutrient gaps: N ${gap.N ?? '—'} kg/ha, P₂O₅ ${gap.P2O5 ?? '—'} kg/ha, K₂O ${gap.K2O ?? '—'} kg/ha.${plan.citation ? ` Source: ${plan.citation}.` : ''}`;

  return {
    id: data.fieldId,
    status: 'Active',
    location: data.location,
    crop: data.crop || 'Unknown',
    stage: currentStageName,
    stageSequence: stages,
    area: data.area_ha ? `${data.area_ha} ha` : '— ha',
    soilType: data.soilType ?? null,
    lat: data.lat,
    lon: data.lon,
    hasSoilTest: data.hasSoilTest ?? false,
    soilHealthScore: data.soilHealthScore ?? null,
    weather: {
      available: weatherKnown,
      rainfall7d: weather.rainfall_mm_next_7d,
      heavy_rain_alert: weather.heavy_rain_alert ?? false,
      condition: weather.condition,
    },
    soil: {
      n: { value: nutrients.n?.current ?? null, score: nScore, label: nutrientLabel(nScore), color: 'bg-blue-500' },
      p: { value: nutrients.p?.current ?? null, score: soil.p_score ?? null, label: nutrientLabel(soil.p_score ?? null), color: 'bg-purple-500' },
      k: { value: nutrients.k?.current ?? null, score: kScore, label: nutrientLabel(kScore), color: 'bg-amber-500' },
      ph: soil.ph ?? null,
      oc: soil.oc_percent ?? null,
      note: description,
    },
    fieldStatus: {
      cropCondition: { label: cropCond, color: cropColor },
      waterStress: { label: waterStress, color: waterColor },
      overall,
    },
    recommendation: {
      action: plan.nextAction || 'Awaiting plan',
      window: plan.applicationWindow?.split('(')[0]?.trim() || '—',
      description,
      quantity: plan.quantity || 'N/A',
      applicationWindow: plan.applicationWindow || 'N/A',
      estimatedCost: plan.estimatedCost ?? null,
      costCitation: plan.costCitation ?? null,
      confidence: plan.confidence || '—',
      citation: plan.citation || '',
      status: plan.status || 'NO_DATA',
      reason: plan.reason ?? null,
      requiredActions: plan.requiredActions || [],
      flags: plan.flags || [],
    },
    timeline: stages,
    activeAlert: data.activeAlert,
  };
}

// ─── Page ─────────────────────────────────────────────────────────────────────
function DashboardField() {
  const { fieldId, setFieldId, fields, fieldsError } = useFieldParam();
  const [field, setField] = React.useState<FieldState | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);
  const [generating, setGenerating] = React.useState(false);
  const [generateError, setGenerateError] = React.useState<string | null>(null);
  const mapCardRef = React.useRef<HTMLDivElement>(null);

  const fetchTwin = React.useCallback((signal?: AbortSignal) => {
    if (!fieldId) return;
    getTwin(fieldId, signal)
      .then((data) => {
        if (signal?.aborted) return;
        setField(mapTwinToFieldState(data));
        setError(null);
        setLastUpdated(new Date());
        setLoading(false);
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        const message = err instanceof ApiError ? err.message : 'Could not reach the AgroTwin backend.';
        setError(message);
        setLoading(false);
      });
  }, [fieldId]);

  // Intentional: switching fields must show a fresh loading state immediately,
  // not derive it from render — eslint-plugin-react-hooks flags this even when correct.
  /* eslint-disable react-hooks/set-state-in-effect */
  React.useEffect(() => {
    setLoading(true);
    const controller = new AbortController();
    fetchTwin(controller.signal);
    // Poll so a backend-side event (e.g. a heavy-rain replan) shows up on its
    // own — the "wow moment" is nobody has to ask the AI anything or refresh.
    const intervalId = setInterval(() => fetchTwin(controller.signal), 15000);
    return () => {
      controller.abort();
      clearInterval(intervalId);
    };
  }, [fetchTwin]);
  /* eslint-enable react-hooks/set-state-in-effect */

  function scrollToMap() {
    mapCardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function handleGenerateRecommendation() {
    setGenerating(true);
    setGenerateError(null);
    recommend(fieldId)
      .then(() => {
        setGenerating(false);
        fetchTwin();
      })
      .catch((err) => {
        setGenerating(false);
        setGenerateError(err instanceof ApiError ? err.message : 'Could not generate a recommendation.');
      });
  }

  // Full-page honest error state: never show stale/fake data as if it were live.
  if (error && !field) {
    return (
      <div className="min-h-screen bg-gray-50 font-sans flex items-center justify-center p-6">
        <div className="max-w-md text-center bg-white border border-red-100 rounded-xl shadow-sm p-8">
          <div className="text-3xl mb-3">⚠️</div>
          <h2 className="text-lg font-bold text-gray-900 mb-2">Can&apos;t reach the backend</h2>
          <p className="text-sm text-gray-500 mb-4">{error}</p>
          <button
            onClick={() => fetchTwin()}
            className="bg-gray-900 hover:bg-gray-800 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (loading && !field) {
    return (
      <div className="min-h-screen bg-gray-50 font-sans flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-500 text-sm">
          <span className="inline-block w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
          Loading field data…
        </div>
      </div>
    );
  }

  if (!field) return null;

  return (
    <div className="min-h-screen bg-gray-50 font-sans">

      {error && (
        <div className="bg-red-50 border-b border-red-200 text-red-700 text-xs px-4 py-2 text-center">
          Connection to backend lost — showing last known data
          {lastUpdated && ` from ${lastUpdated.toLocaleTimeString()}`}.{' '}
          <button onClick={() => fetchTwin()} className="underline font-semibold">Retry</button>
        </div>
      )}

      {/* ── Field selector bar ── */}
      <div className="bg-white border-b border-gray-100 px-4 md:px-6 py-2.5 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">Field:</span>
          {fields.length > 0 ? (
            <FieldSelector fieldId={fieldId} fields={fields} onChange={setFieldId} />
          ) : (
            <span className="text-xs text-gray-400">{fieldsError ? `Field list unavailable (${fieldsError})` : 'Loading fields…'}</span>
          )}
        </div>
        <Link
          href={`/upload?field=${encodeURIComponent(fieldId)}`}
          className="inline-flex items-center gap-1.5 bg-gray-900 hover:bg-gray-800 text-white text-xs font-semibold px-3 py-1.5 rounded-md transition"
        >
          📤 Upload Soil Report
        </Link>
      </div>

      {/* ── Gate: no soil report on file for this field yet ── */}
      {!field.hasSoilTest && (
        <div className="min-h-[70vh] flex items-center justify-center p-6">
          <div className="max-w-md text-center bg-white border border-gray-100 rounded-xl shadow-sm p-8">
            <div className="text-4xl mb-3">🧪</div>
            <h2 className="text-lg font-bold text-gray-900 mb-2">No soil report on file for {field.id}</h2>
            <p className="text-sm text-gray-500 mb-5">
              The digital twin needs at least one soil test before it can show nutrient levels, a
              fertilizer recommendation, or a field health score. Upload a soil health card to unlock
              this field&apos;s dashboard.
            </p>
            <Link
              href={`/upload?field=${encodeURIComponent(field.id)}`}
              className="inline-flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition"
            >
              📤 Upload Soil Report
            </Link>
          </div>
        </div>
      )}

      {/* ── Hero / Field Overview Banner ── */}
      {field.hasSoilTest && (<>
      <div className="relative w-full h-56 md:h-72 overflow-hidden">
        <img
          src="/image.png"
          alt="Field overview"
          className="absolute inset-0 w-full h-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />

        <div className="absolute top-4 left-5 flex items-center gap-2 text-white/80 text-xs font-semibold uppercase tracking-widest">
          <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2z"/></svg>
          Field Overview
        </div>

        <button
          onClick={scrollToMap}
          className="absolute top-4 right-5 flex items-center gap-1.5 bg-white/90 text-gray-800 text-xs font-semibold px-3 py-1.5 rounded-full shadow hover:bg-white transition"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          View on Map
        </button>

        <div className="absolute bottom-16 left-5 md:bottom-20">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl md:text-4xl font-bold text-white">Field {field.id}</h1>
            <span className="bg-green-500 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">{field.status}</span>
          </div>
          <div className="flex items-center gap-1.5 text-white/80 text-sm">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
            {field.location || 'Location not provided'}
          </div>
        </div>

        {/* Field meta chips */}
        <div className="absolute bottom-4 left-5 flex flex-wrap gap-4">
          {[
            { icon: '🌾', label: 'Crop', value: field.crop },
            { icon: '📅', label: 'Stage', value: field.stage },
            { icon: '📐', label: 'Area', value: field.area },
            { icon: '🪨', label: 'Soil Type', value: field.soilType || 'Not recorded' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/20 rounded-lg px-3 py-2">
              <span className="text-base">{item.icon}</span>
              <div>
                <div className="text-white/60 text-[10px] leading-none">{item.label}</div>
                <div className="text-white text-xs font-semibold whitespace-pre-line leading-snug">{item.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Weather widget — only rendered from a real weather_agent snapshot for this field */}
        <div className="absolute bottom-4 right-5 hidden md:flex items-center gap-4 bg-white/15 backdrop-blur-md border border-white/20 rounded-xl px-5 py-3">
          {field.weather.available ? (
            <>
              <div className="max-w-[220px]">
                <div className="text-white/70 text-[10px] uppercase tracking-wide mb-0.5">Weather agent</div>
                <div className="text-white text-xs">{field.weather.condition}</div>
              </div>
              <div className="text-white/80 text-xs">
                <div className="flex justify-between gap-6"><span>Rain (7d)</span><span className="font-semibold text-white">{field.weather.rainfall7d} mm</span></div>
              </div>
            </>
          ) : (
            <div className="text-white/70 text-xs">Weather unavailable for this field</div>
          )}
        </div>
      </div>

      {/* ── Main Grid ── */}
      <div className="p-4 md:p-6 grid grid-cols-1 lg:grid-cols-4 gap-4">

        {/* Soil Health */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">🌱</span>
              <span className="font-semibold text-gray-800 text-sm">Soil Health</span>
            </div>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
              field.soilHealthScore == null ? 'text-gray-500 bg-gray-50 border-gray-200' :
              field.soilHealthScore >= 60 ? 'text-green-600 bg-green-50 border-green-200' :
              field.soilHealthScore >= 35 ? 'text-amber-600 bg-amber-50 border-amber-200' :
              'text-red-600 bg-red-50 border-red-200'
            }`}>{field.soilHealthScore == null ? 'Not available' : `Score: ${field.soilHealthScore}/100`}</span>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: 'Nitrogen (N)', val: field.soil.n.value, score: field.soil.n.score, statusLabel: field.soil.n.label, statusColor: 'text-blue-500', barColor: 'bg-blue-500' },
              { label: 'Phosphorus (P)', val: field.soil.p.value, score: field.soil.p.score, statusLabel: field.soil.p.label, statusColor: 'text-purple-500', barColor: 'bg-purple-500' },
              { label: 'Potassium (K)', val: field.soil.k.value, score: field.soil.k.score, statusLabel: field.soil.k.label, statusColor: 'text-amber-500', barColor: 'bg-amber-500' },
            ].map((n) => (
              <div key={n.label}>
                <div className="text-[10px] text-gray-500 mb-1">{n.label}</div>
                <div className="text-sm font-bold text-gray-800">
                  {n.val ?? '—'} <span className="text-gray-400 font-normal text-[10px]">kg/ha</span>
                </div>
                <div className="h-1.5 w-full bg-gray-100 rounded-full mt-1 mb-1">
                  <div className={`h-1.5 ${n.barColor} rounded-full`} style={{ width: `${n.score ?? 0}%` }} />
                </div>
                <div className={`text-[10px] font-semibold ${n.score == null ? 'text-gray-400' : n.statusColor}`}>{n.statusLabel}</div>
              </div>
            ))}
          </div>

          {(field.soil.ph || field.soil.oc) && (
            <div className="flex gap-3 text-[10px] text-gray-500 mb-3">
              {field.soil.ph && <span>pH: <strong className="text-gray-700">{field.soil.ph}</strong></span>}
              {field.soil.oc && <span>OC: <strong className="text-gray-700">{field.soil.oc}%</strong></span>}
            </div>
          )}

          <div className="flex items-start gap-2 bg-green-50 rounded-lg p-3 text-xs text-gray-600 leading-relaxed">
            <span className="text-green-600 mt-0.5">🌿</span>
            <span>{field.soil.note}</span>
          </div>
        </div>

        {/* Weather Forecast — real rainfall_mm_next_7d only, no fabricated daily series */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">⛅</span>
              <span className="font-semibold text-gray-800 text-sm">Weather <span className="text-gray-400 font-normal">(Next 7 Days)</span></span>
            </div>
          </div>

          {field.weather.available ? (
            <>
              <div className="mb-4">
                <div className="flex items-center gap-3">
                  <div>
                    <div className="text-xs text-gray-500 mb-0.5">Forecast rainfall</div>
                    <div className="text-3xl font-bold text-gray-800">{field.weather.rainfall7d} mm</div>
                  </div>
                  <div className={`border rounded-lg px-2 py-1 text-xs font-semibold ${
                    field.weather.heavy_rain_alert
                      ? 'bg-red-50 border-red-200 text-red-700'
                      : 'bg-green-50 border-green-200 text-green-700'
                  }`}>
                    {field.weather.heavy_rain_alert ? '⚠ Heavy rain' : '✓ Suitable for application'}
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-400">Source: Open-Meteo via weather agent</div>
              <div className="text-[10px] text-gray-300 mt-1">Daily breakdown unavailable — only the 7-day total is reported by the API.</div>
            </>
          ) : (
            <div className="text-sm text-gray-400 italic py-4">
              Weather unavailable — no weather agent run has been recorded for this field yet.
            </div>
          )}
        </div>

        {/* Field Status — derived from real N sufficiency + weather_agent */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">🌿</span>
            <span className="font-semibold text-gray-800 text-sm">Field Status</span>
          </div>

          <div className="space-y-3">
            {[
              { name: 'Crop condition', value: field.fieldStatus.cropCondition.label, color: field.fieldStatus.cropCondition.color },
              { name: 'Water stress', value: field.fieldStatus.waterStress.label, color: field.fieldStatus.waterStress.color },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <span className="text-xs text-gray-500">{item.name}</span>
                <div className="flex items-center gap-1.5">
                  <StatusDot color={item.color} />
                  <span className={`text-xs font-semibold ${item.color}`}>{item.value}</span>
                </div>
              </div>
            ))}
            {/* No pest/disease detection agent exists — never fabricate a risk level. */}
            {[
              { name: 'Pest risk' },
              { name: 'Disease risk' },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <span className="text-xs text-gray-500">{item.name}</span>
                <span className="text-xs font-semibold text-gray-400">Not assessed</span>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">Overall status</span>
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${
              field.fieldStatus.overall === 'Healthy'
                ? 'bg-green-100 text-green-700'
                : field.fieldStatus.overall === 'Unknown'
                ? 'bg-gray-100 text-gray-500'
                : 'bg-amber-100 text-amber-700'
            }`}>{field.fieldStatus.overall}</span>
          </div>
        </div>

        {/* Field Location — only rendered when the field has a real recorded lat/lon */}
        <div ref={mapCardRef} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📍</span>
              <span className="font-semibold text-gray-800 text-sm">Field Location</span>
            </div>
            {field.lat != null && field.lon != null && (
              <a
                href={`https://www.google.com/maps?q=${field.lat},${field.lon}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] font-semibold text-gray-500 hover:text-green-700 transition underline"
              >
                Open in Google Maps ↗
              </a>
            )}
          </div>
          {field.lat != null && field.lon != null ? (
            <div className="relative flex-1 rounded-lg overflow-hidden min-h-[160px]">
              <FieldMap
                lat={field.lat}
                lng={field.lon}
                fieldId={field.id}
                areaLabel={field.area !== '— ha' ? field.area : null}
                zoom={14}
                className="w-full h-full min-h-[160px]"
              />
            </div>
          ) : (
            <div className="flex-1 min-h-[160px] rounded-lg bg-gray-50 border border-dashed border-gray-200 flex items-center justify-center text-xs text-gray-400 italic text-center px-4">
              Location not provided for this field.
            </div>
          )}
        </div>

        {/* Next Recommended Action — real pipeline result */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          {field.recommendation.status === 'ABSTAIN' ? (
            <div className="flex items-start gap-3">
              <span className="text-2xl mt-0.5">⚠️</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-red-50 text-red-700 border border-red-200 text-xs font-bold px-2 py-0.5 rounded-full">
                    ⚠ LOW CONFIDENCE — ABSTAINED
                  </span>
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">A reliable fertilizer plan cannot currently be produced</h2>
                {field.recommendation.reason && (
                  <p className="text-sm text-gray-600 mb-3">{field.recommendation.reason}</p>
                )}
                {field.recommendation.requiredActions.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-gray-500 mb-1">Required:</div>
                    <ul className="text-sm text-gray-700 list-disc list-inside space-y-0.5">
                      {field.recommendation.requiredActions.map((action, i) => (
                        <li key={i}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ) : field.recommendation.status === 'NO_DATA' ? (
            <div className="flex items-start gap-3 text-gray-500">
              <span className="text-2xl mt-0.5">🌱</span>
              <div>
                <h2 className="text-lg font-bold text-gray-700 mb-1">Soil data confirmed. No recommendation has been generated yet.</h2>
                <p className="text-sm mb-3">Run the recommendation pipeline to get an evidence-backed fertilizer plan for this field.</p>
                {generateError && (
                  <p className="text-sm text-red-600 mb-3">{generateError}</p>
                )}
                <button
                  onClick={handleGenerateRecommendation}
                  disabled={generating}
                  className="inline-flex items-center gap-2 bg-gray-900 hover:bg-gray-800 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition"
                >
                  {generating ? 'Generating…' : 'Generate Recommendation'}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-4">
              <span className="text-2xl mt-0.5">🌱</span>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="text-xs text-gray-500 font-medium">Next Recommended Action</span>
                  <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full">{field.recommendation.window}</span>
                  {field.recommendation.confidence && (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${confidenceBadgeClass(field.recommendation.confidence)}`}>
                      Confidence: {field.recommendation.confidence}
                    </span>
                  )}
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{field.recommendation.action}</h2>
                <p className="text-sm text-gray-500 leading-relaxed mb-3 max-w-xl">{field.recommendation.description}</p>
                {(field.recommendation.confidence === 'LOW' || field.recommendation.confidence === 'MEDIUM') && field.recommendation.flags.length > 0 && (
                  <div className="mb-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <div className="text-xs font-semibold text-amber-700 mb-1">⚠ Reasons for reduced confidence:</div>
                    <ul className="text-xs text-amber-800 list-disc list-inside space-y-0.5">
                      {field.recommendation.flags.map((flag, i) => (
                        <li key={i}>{flag}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {field.recommendation.citation && (
                  <p className="text-[10px] text-gray-400 italic mb-4">Source: {field.recommendation.citation}</p>
                )}
                <Link href={`/simulator?field=${encodeURIComponent(field.id)}`} className="inline-flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition">
                  Simulate in What-If
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                </Link>
              </div>

              {/* Real fertilizer quantities */}
              <div className="hidden md:flex flex-col gap-4 min-w-[180px] text-sm">
                <div>
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-0.5"><span>📦</span> Quantity</div>
                  <div className="font-bold text-gray-800 text-xs leading-relaxed">{field.recommendation.quantity}</div>
                </div>
                <div>
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-0.5"><span>📅</span> Application window</div>
                  <div className="font-bold text-gray-800 text-xs">{field.recommendation.applicationWindow}</div>
                </div>
                <div>
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-0.5"><span>💰</span> Est. Cost</div>
                  <div className="font-bold text-gray-800">
                    {field.recommendation.estimatedCost != null ? `₹${Math.round(field.recommendation.estimatedCost).toLocaleString()}` : 'N/A'}
                  </div>
                  {field.recommendation.costCitation && (
                    <div className="text-[9px] text-gray-400 mt-0.5 leading-tight">Engineering-default estimate, not a sourced price.</div>
                  )}
                </div>
              </div>

              <div className="hidden lg:block w-32 h-32 rounded-lg overflow-hidden flex-shrink-0">
                <img src="/image copy 4.png" alt={`${field.crop} crop`} className="w-full h-full object-cover" />
              </div>
            </div>
          )}
        </div>

        {/* Recent Insights — real activeAlert only, honest empty state otherwise */}
        <div className="lg:row-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">💡</span>
              <span className="font-semibold text-gray-800 text-sm">Recent Insights</span>
            </div>
          </div>

          <div className="flex-1 space-y-3">
            {field.activeAlert ? (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-50/50 border border-amber-100">
                <span className="text-xl">🔔</span>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-gray-800 leading-snug mb-0.5">{field.activeAlert.title}</div>
                  <div className="text-[10px] text-gray-500 leading-snug">{field.activeAlert.description}</div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-400 italic py-4 text-center">No recent alerts for this field.</div>
            )}
          </div>
        </div>

        {/* Crop Stage Timeline — shared component, read-only, built from real stageSequence */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-lg">🌱</span>
            <span className="font-semibold text-gray-800 text-sm">Crop Stage Timeline</span>
            <span className="text-xs text-gray-400 ml-1">— {field.crop} · Current: {field.stage}</span>
          </div>
          {field.timeline.length > 0 ? (
            <StageTimeline stages={field.timeline} currentStage={field.stage} readOnly />
          ) : (
            <div className="text-xs text-gray-400 italic">No stage sequence available for this crop.</div>
          )}
        </div>

      </div>
      </>)}
    </div>
  );
}

function DashboardContent() {
  const { fieldId, setFieldId, fields, fieldsError } = useFieldParam();
  if (!fieldId) return <FieldOnboarding fields={fields} fieldsError={fieldsError} onSelect={setFieldId} />;
  return <DashboardField key={fieldId} />;
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center text-sm text-gray-500">Loading…</div>}>
      <DashboardContent />
    </Suspense>
  );
}
