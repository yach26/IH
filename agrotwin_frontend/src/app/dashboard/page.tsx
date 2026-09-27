"use client";

import React from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';

const FieldMap = dynamic(() => import('@/components/ui/FieldMap'), { ssr: false });
const FullscreenMap = dynamic(() => import('@/components/ui/FieldMap'), { ssr: false });

// ─── Types ───────────────────────────────────────────────────────────────────
type FieldMeta = {
  field_code: string;
  area_ha: number;
  lat: number;
  lon: number;
  crop_code: string;
  current_stage: string;
};

type NutrientEntry = { value: number; score: number; label: string };
type FieldState = {
  id: string;
  status: string;
  location: string;
  crop: string;
  stage: string;
  stageSequence: string[];
  area: string;
  soilType: string;
  lat: number;
  lon: number;
  soilHealthScore: number;
  weather: { temp: number; condition: string; humidity: number; wind: number; rainfall7d: number; heavy_rain_alert: boolean };
  soil: { n: NutrientEntry; p: NutrientEntry; k: NutrientEntry; ph: number | null; oc: number | null; note: string };
  fieldStatus: {
    cropCondition: { label: string; color: string };
    waterStress: { label: string; color: string };
    pestRisk: { label: string; color: string };
    diseaseRisk: { label: string; color: string };
    overall: string;
  };
  recommendation: {
    action: string; window: string; description: string; quantity: string;
    applicationWindow: string; expectedBenefit: string;
    estimatedCost: number; confidence: string; citation: string;
    soilGap: { n: string, p: string, k: string };
  };
  timeline: { name: string; done: boolean; current?: boolean }[];
  insights: { title: string; time: string; desc: string; img: string }[];
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
function nutrientLabel(score: number) {
  if (score >= 80) return 'High';
  if (score >= 45) return 'Moderate';
  return 'Low';
}

function nutrientColor(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score >= 45) return 'text-amber-600';
  return 'text-red-500';
}

function StatusDot({ color }: { color: string }) {
  const map: Record<string, string> = {
    'text-green-500': 'bg-green-500', 'text-amber-500': 'bg-amber-500',
    'text-gray-400': 'bg-gray-300', 'text-red-500': 'bg-red-500',
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${map[color] || 'bg-gray-400'}`} />;
}

const SKELETON: FieldState = {
  id: '…', status: 'Active', location: 'Kolhapur, Maharashtra',
  crop: 'Loading…', stage: 'Loading…',
  stageSequence: ['Land Prep', 'Germination', 'Tillering', 'Grand Growth', 'Ripening', 'Harvest'],
  area: '— ha', soilType: '—', lat: 16.0644, lon: 74.1352, soilHealthScore: 0,
  weather: { temp: 28, condition: 'Loading…', humidity: 75, wind: 10, rainfall7d: 0, heavy_rain_alert: false },
  soil: {
    n: { value: 0, score: 0, label: '…' }, p: { value: 0, score: 0, label: '…' },
    k: { value: 0, score: 0, label: '…' }, ph: null, oc: null, note: 'Fetching soil data…',
  },
  fieldStatus: {
    cropCondition: { label: '…', color: 'text-gray-400' }, waterStress: { label: '…', color: 'text-gray-400' },
    pestRisk: { label: 'Moderate', color: 'text-amber-500' }, diseaseRisk: { label: 'Low', color: 'text-gray-400' }, overall: '…',
  },
  recommendation: {
    action: 'Loading…', window: '…', description: 'Fetching AI recommendation…',
    quantity: '—', applicationWindow: '—', expectedBenefit: '—', estimatedCost: 0, confidence: '—', citation: '',
    soilGap: { n: '—', p: '—', k: '—' },
  },
  timeline: [],
  insights: [
    { title: 'Rainfall forecast updated', time: '2 hours ago', desc: 'Next 7-day forecast available.', img: '/image copy 2.png' },
    { title: 'Soil analysis loaded', time: 'Today', desc: 'Real Polgaon SHC data ingested.', img: '/image copy 3.png' },
    { title: 'Recommendation ready', time: 'Today', desc: 'AI pipeline has generated your plan.', img: '/image copy 4.png' },
  ],
};

function buildFieldState(data: Record<string, unknown>): FieldState {
  const nutrients = (data.nutrients as Record<string, Record<string, number>>) || {};
  const soil = (data.soilDetail as Record<string, number | null>) || {};
  const plan = (data.currentPlan as Record<string, unknown>) || {};
  const weather = (data.weather as Record<string, unknown>) || {};
  const stages: string[] = (data.stageSequence as string[]) || SKELETON.stageSequence;
  const currentStageName = (data.growthStage as string) || '';

  const nScore = (soil.n_score as number) ?? 0;
  const pScore = (soil.p_score as number) ?? 0;
  const kScore = (soil.k_score as number) ?? 0;
  const rainfallOk = !(weather.heavy_rain_alert as boolean);
  const nSufficient = nScore >= 60;

  const currentIdx = stages.findIndex(s => s.toLowerCase() === currentStageName.toLowerCase());
  const timeline = stages.map((name, i) => ({
    name, done: i < (currentIdx >= 0 ? currentIdx : stages.length - 2),
    current: i === (currentIdx >= 0 ? currentIdx : stages.length - 2),
  }));

  const gap = (plan.soilGap as Record<string, number>) || {};
  // Simplified description for better readability
  const desc = `Targeting an optimal yield of 80-100 t/ha based on current growth stage and local soil health profile.`;

  return {
    id: (data.fieldId as string) || 'REAL-001',
    status: 'Active',
    location: (data.location as string) || 'Kolhapur, Maharashtra',
    crop: (data.crop as string) || 'Sugarcane',
    stage: currentStageName,
    stageSequence: stages,
    area: data.area_ha ? `${data.area_ha} ha` : '2 ha',
    soilType: 'Laterite / Clay Loam',
    lat: (data.lat as number) || 16.0644,
    lon: (data.lon as number) || 74.1352,
    soilHealthScore: (data.soilHealthScore as number) ?? 0,
    weather: {
      temp: 28, condition: (weather.condition as string) || 'Clear',
      humidity: 75, wind: 10,
      rainfall7d: (weather.rainfall_mm_next_7d as number) ?? 17,
      heavy_rain_alert: (weather.heavy_rain_alert as boolean) ?? false,
    },
    soil: {
      n: { value: nutrients.n?.current ?? 0, score: nScore, label: nutrientLabel(nScore) },
      p: { value: nutrients.p?.current ?? 0, score: pScore, label: nutrientLabel(pScore) },
      k: { value: nutrients.k?.current ?? 0, score: kScore, label: nutrientLabel(kScore) },
      ph: (soil.ph as number) ?? null,
      oc: (soil.oc_percent as number) ?? null,
      note: `Polgaon SHC — N=${nutrients.n?.current} kg/ha, P=${nutrients.p?.current} kg/ha, K=${nutrients.k?.current} kg/ha.`,
    },
    fieldStatus: {
      cropCondition: { label: nSufficient ? 'Good' : 'Moderate', color: nSufficient ? 'text-green-500' : 'text-amber-500' },
      waterStress: { label: rainfallOk ? 'Low' : 'High', color: rainfallOk ? 'text-gray-400' : 'text-red-500' },
      pestRisk: { label: 'Moderate', color: 'text-amber-500' },
      diseaseRisk: { label: 'Low', color: 'text-gray-400' },
      overall: (nSufficient && rainfallOk) ? 'Healthy' : 'Needs Attention',
    },
    recommendation: {
      action: (plan.nextAction as string) || 'DAP + Urea + MOP',
      window: ((plan.applicationWindow as string) || '').split('(')[0]?.trim() || 'This week',
      description: desc,
      quantity: (plan.quantity as string) || '—',
      applicationWindow: (plan.applicationWindow as string) || '—',
      expectedBenefit: 'Meet seasonal NPK requirements; target 80-100 t/ha yield',
      estimatedCost: (plan.estimatedCost as number) ?? 0,
      confidence: (plan.confidence as string) || '—',
      citation: (plan.citation as string) || '',
      soilGap: {
        n: gap.N !== undefined ? String(gap.N) : '—',
        p: gap.P2O5 !== undefined ? String(gap.P2O5) : '—',
        k: gap.K2O !== undefined ? String(gap.K2O) : '—'
      }
    },
    timeline,
    insights: [
      ...(data.activeAlert ? [{ title: String((data.activeAlert as Record<string, unknown>).title || 'Alert'), time: 'Just now', desc: String((data.activeAlert as Record<string, unknown>).description || ''), img: '/image copy 2.png' }] : []),
      ...SKELETON.insights,
    ],
  };
}

// ─── Fullscreen Map Modal ─────────────────────────────────────────────────────
function MapModal({ field, allFields, onClose }: { field: FieldState; allFields: FieldMeta[]; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[300] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl overflow-hidden w-full max-w-4xl shadow-2xl flex flex-col" style={{ height: '80vh' }} onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <div className="font-bold text-gray-900">Field Map — {field.id}</div>
            <div className="text-xs text-gray-500">{field.crop} · {field.stage} · {field.area} · Lat {field.lat.toFixed(4)}, Lon {field.lon.toFixed(4)}</div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 transition text-gray-500 hover:text-gray-900">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <div className="flex-1 relative">
          <FullscreenMap lat={field.lat} lng={field.lon} fieldId={field.id} zoom={13} className="w-full h-full" />
          {/* Field info chips overlaid on map */}
          <div className="absolute top-3 left-3 flex flex-col gap-2 z-[400]">
            {allFields.map(f => (
              <div key={f.field_code} className={`px-3 py-1.5 rounded-full text-xs font-bold shadow border ${f.field_code === field.id ? 'bg-green-600 text-white border-green-600' : 'bg-white text-gray-700 border-gray-200'}`}>
                {f.field_code} · {f.area_ha} ha
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Field Selector Pill ──────────────────────────────────────────────────────
function FieldSelectorBar({ fields, activeId, onChange }: { fields: FieldMeta[]; activeId: string; onChange: (id: string) => void }) {
  return (
    <div className="bg-white border-b border-gray-100 px-4 py-2 flex items-center gap-2 overflow-x-auto">
      <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mr-1 whitespace-nowrap">Switch Field</span>
      {fields.map(f => (
        <button
          key={f.field_code}
          onClick={() => onChange(f.field_code)}
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border transition whitespace-nowrap ${
            f.field_code === activeId
              ? 'bg-green-600 text-white border-green-600 shadow-sm'
              : 'bg-white text-gray-600 border-gray-200 hover:border-green-400 hover:text-green-700'
          }`}
        >
          {f.field_code}
          <span className="opacity-70">{f.area_ha}ha</span>
        </button>
      ))}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [allFields, setAllFields] = React.useState<FieldMeta[]>([]);
  const [activeFieldId, setActiveFieldId] = React.useState('REAL-001');
  const [field, setField] = React.useState<FieldState>(SKELETON);
  const [loading, setLoading] = React.useState(true);
  const [showMap, setShowMap] = React.useState(false);

  // Load all fields list once
  React.useEffect(() => {
    const apiHost = window.location.hostname;
    fetch(`http://${apiHost}:8000/fields`)
      .then(r => r.json())
      .then((data: FieldMeta[]) => {
        if (Array.isArray(data) && data.length > 0) setAllFields(data);
      })
      .catch(console.error);
  }, []);

  // Load twin data whenever active field changes
  React.useEffect(() => {
    const apiHost = window.location.hostname;
    setLoading(true);
    setField(SKELETON);
    fetch(`http://${apiHost}:8000/fields/${activeFieldId}/twin`)
      .then(r => r.json())
      .then(data => {
        setField(buildFieldState(data));
        setLoading(false);
      })
      .catch(err => { console.error('Twin fetch error:', err); setLoading(false); });
  }, [activeFieldId]);

  const maxForecastBars = [12, 5, 18, 28, 42, 10, 6];

  return (
    <div className="min-h-screen bg-gray-50 font-sans">

      {/* Map Modal */}
      {showMap && <MapModal field={field} allFields={allFields} onClose={() => setShowMap(false)} />}

      {/* ── Hero Banner ── */}
      <div className="relative w-full h-56 md:h-72 overflow-hidden">
        <img src="/image.png" alt="Field overview" className="absolute inset-0 w-full h-full object-cover object-center" />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />

        <div className="absolute top-4 left-5 flex items-center gap-2 text-white/80 text-xs font-semibold uppercase tracking-widest">
          <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2z"/></svg>
          Field Overview
        </div>

        {/* View on Map — now functional */}
        <button
          onClick={() => setShowMap(true)}
          className="absolute top-4 right-5 flex items-center gap-1.5 bg-white/90 text-gray-800 text-xs font-semibold px-3 py-1.5 rounded-full shadow hover:bg-white transition"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          View on Map
        </button>

        <div className="absolute bottom-16 left-5 md:bottom-20">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl md:text-4xl font-bold text-white">Field {field.id}</h1>
            <span className={`text-white text-xs font-bold px-2.5 py-0.5 rounded-full ${loading ? 'bg-gray-500' : 'bg-green-500'}`}>
              {loading ? 'Loading…' : field.status}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-white/80 text-sm">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
            {field.location}
          </div>
        </div>

        {/* Field Meta Chips */}
        <div className="absolute bottom-4 left-5 flex flex-wrap gap-3">
          {[
            { icon: '🌾', label: 'Crop', value: field.crop },
            { icon: '📅', label: 'Stage', value: field.stage },
            { icon: '📐', label: 'Area', value: field.area },
            { icon: '🪨', label: 'Soil', value: field.soilType },
          ].map(item => (
            <div key={item.label} className="flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/20 rounded-lg px-3 py-2">
              <span className="text-base">{item.icon}</span>
              <div>
                <div className="text-white/60 text-[10px] leading-none">{item.label}</div>
                <div className="text-white text-xs font-semibold">{item.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Weather Widget */}
        <div className="absolute bottom-4 right-5 hidden md:flex items-center gap-4 bg-white/15 backdrop-blur-md border border-white/20 rounded-xl px-5 py-3">
          <div>
            <div className="text-white text-3xl font-bold">{field.weather.temp}°C</div>
            <div className="text-white/70 text-xs">{field.weather.condition}</div>
          </div>
          <div className="text-white/80 text-xs space-y-1">
            <div className="flex justify-between gap-6"><span>Humidity</span><span className="font-semibold text-white">{field.weather.humidity}%</span></div>
            <div className="flex justify-between gap-6"><span>Wind</span><span className="font-semibold text-white">{field.weather.wind} km/h</span></div>
            <div className="flex justify-between gap-6"><span>Rain 7d</span><span className="font-semibold text-white">{field.weather.rainfall7d} mm</span></div>
          </div>
        </div>
      </div>

      {/* ── Field Switcher Bar ── */}
      {allFields.length > 0 && (
        <FieldSelectorBar fields={allFields} activeId={activeFieldId} onChange={setActiveFieldId} />
      )}

      {/* ── Main Grid ── */}
      <div className={`p-4 md:p-6 grid grid-cols-1 lg:grid-cols-4 gap-4 transition-opacity ${loading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>

        {/* Soil Health */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">🌱</span>
              <span className="font-semibold text-gray-800 text-sm">Soil Health</span>
            </div>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
              field.soilHealthScore >= 60 ? 'text-green-600 bg-green-50 border-green-200' :
              field.soilHealthScore >= 35 ? 'text-amber-600 bg-amber-50 border-amber-200' :
              'text-red-600 bg-red-50 border-red-200'
            }`}>Score: {field.soilHealthScore}/100</span>
          </div>
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: 'Nitrogen (N)', entry: field.soil.n, barColor: 'bg-blue-500' },
              { label: 'Phosphorus (P)', entry: field.soil.p, barColor: 'bg-purple-500' },
              { label: 'Potassium (K)', entry: field.soil.k, barColor: 'bg-amber-500' },
            ].map(({ label, entry, barColor }) => (
              <div key={label}>
                <div className="text-[10px] text-gray-500 mb-1">{label}</div>
                <div className="text-sm font-bold text-gray-800">{entry.value} <span className="text-gray-400 font-normal text-[10px]">kg/ha</span></div>
                <div className="h-1.5 w-full bg-gray-100 rounded-full mt-1 mb-1">
                  <div className={`h-1.5 ${barColor} rounded-full transition-all duration-500`} style={{ width: `${entry.score}%` }} />
                </div>
                <div className={`text-[10px] font-semibold ${nutrientColor(entry.score)}`}>{entry.label}</div>
              </div>
            ))}
          </div>
          {(field.soil.ph || field.soil.oc) && (
            <div className="flex gap-4 text-[10px] text-gray-500 mb-3">
              {field.soil.ph && <span>pH: <strong className="text-gray-700">{field.soil.ph}</strong></span>}
              {field.soil.oc && <span>OC: <strong className="text-gray-700">{field.soil.oc}%</strong></span>}
            </div>
          )}
          <div className="flex items-start gap-2 bg-green-50 rounded-lg p-3 text-xs text-gray-600 leading-relaxed">
            <span className="text-green-600 mt-0.5">🌿</span>
            <span>{field.soil.note}</span>
          </div>
        </div>

        {/* Weather Forecast */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">⛅</span>
            <span className="font-semibold text-gray-800 text-sm">Weather <span className="text-gray-400 font-normal">(Next 7 Days)</span></span>
          </div>
          <div className="mb-4">
            <div className="flex items-center gap-3">
              <div>
                <div className="text-xs text-gray-500 mb-0.5">Forecast rainfall</div>
                <div className="text-3xl font-bold text-gray-800">{field.weather.rainfall7d} mm</div>
              </div>
              <div className={`border rounded-lg px-2 py-1 text-xs font-semibold ${field.weather.heavy_rain_alert ? 'bg-red-50 border-red-200 text-red-700' : 'bg-green-50 border-green-200 text-green-700'}`}>
                {field.weather.heavy_rain_alert ? '⚠ Heavy rain' : '✓ Clear for application'}
              </div>
            </div>
            <div className="text-[10px] text-gray-400 mt-1">Source: Open-Meteo via weather agent</div>
          </div>
          <div className="flex items-end gap-1 h-16">
            {maxForecastBars.map((mm, i) => (
              <div key={i} className="flex flex-col items-center flex-1 gap-1">
                <div className="w-full bg-green-500 rounded-t-sm" style={{ height: `${Math.max(4, (mm / 42) * 48)}px` }} />
                <div className="text-[9px] text-gray-500">{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i]}</div>
                <div className="text-[9px] font-semibold text-gray-700">{mm}mm</div>
              </div>
            ))}
          </div>
        </div>

        {/* Field Status */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">🌿</span>
            <span className="font-semibold text-gray-800 text-sm">Field Status</span>
          </div>
          <div className="space-y-3">
            {[
              { name: 'Crop condition', ...field.fieldStatus.cropCondition },
              { name: 'Water stress', ...field.fieldStatus.waterStress },
              { name: 'Pest risk', ...field.fieldStatus.pestRisk },
              { name: 'Disease risk', ...field.fieldStatus.diseaseRisk },
            ].map(item => (
              <div key={item.name} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <span className="text-xs text-gray-500">{item.name}</span>
                <div className="flex items-center gap-1.5">
                  <StatusDot color={item.color} />
                  <span className={`text-xs font-semibold ${item.color}`}>{item.label}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">Overall status</span>
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${field.fieldStatus.overall === 'Healthy' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
              {field.fieldStatus.overall}
            </span>
          </div>
        </div>

        {/* Field Location — now opens modal on "View on Map" click */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📍</span>
              <span className="font-semibold text-gray-800 text-sm">Field Location</span>
            </div>
            <button
              onClick={() => setShowMap(true)}
              className="text-[10px] font-semibold text-green-700 hover:text-green-900 border border-green-200 bg-green-50 hover:bg-green-100 px-2 py-1 rounded-md transition"
            >
              Expand ↗
            </button>
          </div>
          <div className="relative flex-1 rounded-lg overflow-hidden min-h-[160px]">
            <FieldMap lat={field.lat} lng={field.lon} fieldId={field.id} zoom={14} className="w-full h-full min-h-[160px]" />
          </div>
          <div className="mt-2 text-[10px] text-gray-400 text-center">
            {field.lat.toFixed(4)}°N, {field.lon.toFixed(4)}°E
          </div>
        </div>

        {/* Recommendation Panel */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-start gap-4">
            <span className="text-2xl mt-0.5">🌱</span>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <span className="text-xs text-purple-700 bg-purple-100 font-bold px-2 py-0.5 rounded flex items-center gap-1 border border-purple-200">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                  RAG-Driven Recommendation Plan
                </span>
                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full">{field.recommendation.window}</span>
                {field.recommendation.confidence && field.recommendation.confidence !== '—' && (
                  <span className="bg-blue-50 text-blue-600 text-xs font-bold px-2 py-0.5 rounded-full border border-blue-200">
                    Confidence: {field.recommendation.confidence}
                  </span>
                )}
              </div>
              <h2 className="text-3xl font-extrabold text-green-900 mb-2">{field.recommendation.action}</h2>
              <p className="text-base text-gray-700 leading-relaxed mb-4 max-w-xl">{field.recommendation.description}</p>
              
              {/* Clean Soil Gap Visualizer */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-100 mb-4 max-w-xl">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Calculated Soil Deficit (To Fill)</p>
                <div className="flex gap-6">
                  <div className="flex-1">
                    <p className="text-[10px] text-gray-500 font-semibold mb-1">Nitrogen (N)</p>
                    <p className="text-lg font-bold text-blue-700">{field.recommendation.soilGap?.n} <span className="text-[10px] text-gray-400 font-normal">kg/ha</span></p>
                  </div>
                  <div className="w-px bg-gray-200" />
                  <div className="flex-1">
                    <p className="text-[10px] text-gray-500 font-semibold mb-1">Phosphorus (P₂O₅)</p>
                    <p className="text-lg font-bold text-purple-700">{field.recommendation.soilGap?.p} <span className="text-[10px] text-gray-400 font-normal">kg/ha</span></p>
                  </div>
                  <div className="w-px bg-gray-200" />
                  <div className="flex-1">
                    <p className="text-[10px] text-gray-500 font-semibold mb-1">Potassium (K₂O)</p>
                    <p className="text-lg font-bold text-amber-700">{field.recommendation.soilGap?.k} <span className="text-[10px] text-gray-400 font-normal">kg/ha</span></p>
                  </div>
                </div>
              </div>

              {field.recommendation.citation && (
                <div className="flex items-center gap-1.5 text-[11px] text-gray-500 bg-white border border-gray-100 px-3 py-1.5 rounded-full inline-flex mb-4">
                  <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                  Source ledger: <span className="font-medium text-gray-700">{field.recommendation.citation.split('/').pop()}</span>
                </div>
              )}
              
              <div className="mt-2">
                <Link href="/simulator" className="inline-flex items-center gap-2 bg-green-700 hover:bg-green-800 text-white text-sm font-semibold px-6 py-3 rounded-lg transition shadow-sm">
                  Simulate in What-If
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
                </Link>
              </div>
            </div>
            <div className="hidden md:flex flex-col gap-4 min-w-[180px] text-sm">
              {[
                { icon: '📦', label: 'Quantity', value: field.recommendation.quantity },
                { icon: '📅', label: 'Window', value: field.recommendation.applicationWindow },
                { icon: '💰', label: 'Est. Cost', value: `₹${field.recommendation.estimatedCost.toLocaleString()}` },
              ].map(s => (
                <div key={s.label}>
                  <div className="flex items-center gap-1.5 text-gray-400 text-xs mb-0.5"><span>{s.icon}</span>{s.label}</div>
                  <div className="font-bold text-gray-800 text-xs leading-relaxed">{s.value}</div>
                </div>
              ))}
            </div>
            <div className="hidden lg:block w-32 h-32 rounded-lg overflow-hidden flex-shrink-0">
              <img src="/image copy 4.png" alt="Crop" className="w-full h-full object-cover" />
            </div>
          </div>
        </div>

        {/* Recent Insights */}
        <div className="lg:row-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">💡</span>
              <span className="font-semibold text-gray-800 text-sm">Recent Insights</span>
            </div>
          </div>
          <div className="flex-1 space-y-3">
            {field.insights.map((ins, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition cursor-pointer">
                <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0">
                  <img src={ins.img} alt={ins.title} className="w-full h-full object-cover" />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-gray-800 leading-snug mb-0.5">{ins.title}</div>
                  <div className="text-[10px] text-gray-400 mb-0.5">{ins.time}</div>
                  <div className="text-[10px] text-gray-500 leading-snug">{ins.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Crop Stage Timeline */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-lg">🌱</span>
            <span className="font-semibold text-gray-800 text-sm">Crop Stage Timeline</span>
            <span className="text-xs text-gray-400 ml-1">— {field.crop} · Current: <strong className="text-green-700">{field.stage}</strong></span>
          </div>
          <div className="relative">
            <div className="absolute top-4 left-0 right-0 h-0.5 bg-gray-200" />
            {field.timeline.length > 0 && (
              <div className="absolute top-4 left-0 h-0.5 bg-green-500 transition-all duration-700"
                style={{ width: `${(Math.max(0, field.timeline.findIndex(s => s.current)) / Math.max(1, field.timeline.length - 1)) * 100}%` }} />
            )}
            <div className="relative grid gap-2" style={{ gridTemplateColumns: `repeat(${field.timeline.length || 6}, minmax(0, 1fr))` }}>
              {field.timeline.map((stage, i) => (
                <div key={i} className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center z-10 text-sm mb-2 transition-colors ${
                    stage.current ? 'bg-green-600 border-2 border-green-600 text-white shadow-lg shadow-green-200'
                    : stage.done ? 'bg-white border-2 border-green-500'
                    : 'bg-white border-2 border-gray-200'
                  }`}>
                    {stage.done && !stage.current
                      ? <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7"/></svg>
                      : <span className={`text-base ${stage.current ? '' : 'opacity-30'}`}>🌿</span>}
                  </div>
                  <div className={`text-center text-[10px] font-semibold ${stage.current ? 'text-green-700' : stage.done ? 'text-gray-600' : 'text-gray-300'}`}>{stage.name}</div>
                  {stage.current && <span className="mt-1 bg-green-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full whitespace-nowrap">Current</span>}
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
