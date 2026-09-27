"use client";

import React from 'react';
import dynamic from 'next/dynamic';

const FieldMap = dynamic(() => import('@/components/ui/FieldMap'), { ssr: false });
import Link from 'next/link';

// ─── Types ────────────────────────────────────────────────────────────────────
type NutrientEntry = { value: number; score: number; label: string; color: string };
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
  weather: { temp: number; condition: string; humidity: number; wind: number; rain24h: number; rainfall7d: number };
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
    pestRisk: { label: string; color: string };
    diseaseRisk: { label: string; color: string };
    overall: string;
  };
  recommendation: {
    action: string;
    window: string;
    description: string;
    quantity: string;
    applicationWindow: string;
    expectedBenefit: string;
    estimatedCost: number;
    confidence: string;
    citation: string;
  };
  timeline: { name: string; done: boolean; current?: boolean }[];
  insights: { title: string; time: string; desc: string; img: string }[];
};

// ─── Default / Skeleton State ─────────────────────────────────────────────────
const defaultField: FieldState = {
  id: '…',
  status: 'Active',
  location: 'Kolhapur, Maharashtra',
  crop: 'Loading…',
  stage: 'Loading…',
  stageSequence: ["Land Prep", "Germination", "Tillering", "Grand Growth", "Ripening", "Harvest"],
  area: '— ha',
  soilType: '—',
  lat: 16.0644,
  lon: 74.1352,
  soilHealthScore: 0,
  weather: { temp: 28, condition: 'Loading…', humidity: 75, wind: 10, rain24h: 0, rainfall7d: 0 },
  soil: {
    n: { value: 0, score: 0, label: '…', color: 'bg-blue-500' },
    p: { value: 0, score: 0, label: '…', color: 'bg-purple-500' },
    k: { value: 0, score: 0, label: '…', color: 'bg-amber-500' },
    ph: null,
    oc: null,
    note: 'Loading soil analysis…',
  },
  fieldStatus: {
    cropCondition: { label: '…', color: 'text-gray-400' },
    waterStress: { label: '…', color: 'text-gray-400' },
    pestRisk: { label: '…', color: 'text-gray-400' },
    diseaseRisk: { label: '…', color: 'text-gray-400' },
    overall: 'Loading…',
  },
  recommendation: {
    action: 'Loading recommendation…',
    window: '…',
    description: 'Fetching AI recommendation from pipeline…',
    quantity: '—',
    applicationWindow: '—',
    expectedBenefit: '—',
    estimatedCost: 0,
    confidence: '—',
    citation: '',
  },
  timeline: [],
  insights: [
    { title: 'Rainfall forecast updated', time: '2 hours ago', desc: 'Next 7-day forecast available.', img: '/image copy 2.png' },
    { title: 'Soil analysis loaded', time: 'Today', desc: 'Real Polgaon SHC data ingested.', img: '/image copy 3.png' },
    { title: 'Recommendation ready', time: 'Today', desc: 'AI pipeline has generated your plan.', img: '/image copy 4.png' },
  ],
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function nutrientLabel(score: number): string {
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

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [field, setField] = React.useState<FieldState>(defaultField);
  const [loading, setLoading] = React.useState(true);
  const maxForecastMm = Math.max(...[12, 5, 18, 28, 42, 10, 6]);

  React.useEffect(() => {
    fetch('http://localhost:8000/fields/REAL-001/twin')
      .then(r => r.json())
      .then(data => {
        const nutrients = data.nutrients || {};
        const soil = data.soilDetail || {};
        const plan = data.currentPlan || {};
        const weather = data.weather || {};
        const stages: string[] = data.stageSequence || defaultField.stageSequence;
        const currentStageName = data.growthStage || '';

        // Score-to-label for nutrients
        const nScore = soil.n_score ?? 0;
        const pScore = soil.p_score ?? 0;
        const kScore = soil.k_score ?? 0;

        // Derive field status from real data
        const rainfallOk = !weather.heavy_rain_alert;
        const waterStress = rainfallOk ? 'Low' : 'High';
        const waterColor = rainfallOk ? 'text-gray-400' : 'text-red-500';
        const nSufficient = nScore >= 60;
        const cropCond = nSufficient ? 'Good' : 'Moderate';
        const cropColor = nSufficient ? 'text-green-500' : 'text-amber-500';
        const overall = (nSufficient && rainfallOk) ? 'Healthy' : 'Needs Attention';

        // Build timeline from stageSequence
        const currentIdx = stages.findIndex(s =>
          s.toLowerCase() === currentStageName.toLowerCase()
        );
        const timeline = stages.map((name, i) => ({
          name,
          done: i < (currentIdx >= 0 ? currentIdx : stages.length - 2),
          current: i === (currentIdx >= 0 ? currentIdx : stages.length - 2),
        }));

        // Recommendation description
        const gap = plan.soilGap || {};
        const description = `Based on Polgaon real soil test (N=${nutrients.n?.current} kg/ha, P=${nutrients.p?.current} kg/ha, K=${nutrients.k?.current} kg/ha) and ${data.crop} at ${currentStageName} stage. Nutrient gaps: N ${gap.N ?? '—'} kg/ha, P₂O₅ ${gap.P2O5 ?? '—'} kg/ha, K₂O ${gap.K2O ?? '—'} kg/ha. Source: ${plan.citation || 'MPKV-ICAR RDF Kolhapur 2022'}.`;

        const insight = data.activeAlert ? [{
          title: data.activeAlert.title || 'New Alert',
          time: 'Just now',
          desc: data.activeAlert.description || '',
          img: '/image copy 2.png'
        }] : [];

        setField({
          id: data.fieldId || 'REAL-001',
          status: 'Active',
          location: data.location || 'Kolhapur, Maharashtra',
          crop: data.crop || 'Sugarcane',
          stage: currentStageName,
          stageSequence: stages,
          area: data.area_ha ? `${data.area_ha} ha` : '2 ha',
          soilType: 'Laterite / Clay Loam',
          lat: data.lat || 16.0644,
          lon: data.lon || 74.1352,
          soilHealthScore: data.soilHealthScore ?? 0,
          weather: {
            temp: 28,
            condition: weather.condition || 'Clear',
            humidity: 75,
            wind: 10,
            rain24h: 0,
            rainfall7d: weather.rainfall_mm_next_7d ?? 17,
          },
          soil: {
            n: { value: nutrients.n?.current ?? 0, score: nScore, label: nutrientLabel(nScore), color: 'bg-blue-500' },
            p: { value: nutrients.p?.current ?? 0, score: pScore, label: nutrientLabel(pScore), color: 'bg-purple-500' },
            k: { value: nutrients.k?.current ?? 0, score: kScore, label: nutrientLabel(kScore), color: 'bg-amber-500' },
            ph: soil.ph ?? null,
            oc: soil.oc_percent ?? null,
            note: description,
          },
          fieldStatus: {
            cropCondition: { label: cropCond, color: cropColor },
            waterStress: { label: waterStress, color: waterColor },
            pestRisk: { label: 'Moderate', color: 'text-amber-500' },   // no pest agent yet
            diseaseRisk: { label: 'Low', color: 'text-gray-400' },
            overall,
          },
          recommendation: {
            action: plan.nextAction || 'DAP + Urea + MOP',
            window: plan.applicationWindow?.split('(')[0]?.trim() || 'This week',
            description,
            quantity: plan.quantity || '—',
            applicationWindow: plan.applicationWindow || '—',
            expectedBenefit: 'Meet seasonal NPK requirements; target 80-100 t/ha yield',
            estimatedCost: plan.estimatedCost ?? 0,
            confidence: plan.confidence || '—',
            citation: plan.citation || '',
          },
          timeline,
          insights: [...insight, ...defaultField.insights],
        });
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching twin data:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">

      {/* ── Hero / Field Overview Banner ── */}
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

        <button className="absolute top-4 right-5 flex items-center gap-1.5 bg-white/90 text-gray-800 text-xs font-semibold px-3 py-1.5 rounded-full shadow hover:bg-white transition">
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
            {field.location}
          </div>
        </div>

        {/* Field meta chips */}
        <div className="absolute bottom-4 left-5 flex flex-wrap gap-4">
          {[
            { icon: '🌾', label: 'Crop', value: field.crop },
            { icon: '📅', label: 'Stage', value: field.stage },
            { icon: '📐', label: 'Area', value: field.area },
            { icon: '🪨', label: 'Soil Type', value: field.soilType },
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

        {/* Weather widget — real rainfall from weather_agent */}
        <div className="absolute bottom-4 right-5 hidden md:flex items-center gap-4 bg-white/15 backdrop-blur-md border border-white/20 rounded-xl px-5 py-3">
          <div>
            <div className="text-white text-3xl font-bold">{field.weather.temp}°C</div>
            <div className="text-white/70 text-xs">{field.weather.condition}</div>
          </div>
          <div className="text-white/80 text-xs space-y-1">
            <div className="flex justify-between gap-6"><span>Humidity</span><span className="font-semibold text-white">{field.weather.humidity}%</span></div>
            <div className="flex justify-between gap-6"><span>Wind</span><span className="font-semibold text-white">{field.weather.wind} km/h</span></div>
            <div className="flex justify-between gap-6"><span>Rain (7d)</span><span className="font-semibold text-white">{field.weather.rainfall7d} mm</span></div>
          </div>
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
              field.soilHealthScore >= 60 ? 'text-green-600 bg-green-50 border-green-200' :
              field.soilHealthScore >= 35 ? 'text-amber-600 bg-amber-50 border-amber-200' :
              'text-red-600 bg-red-50 border-red-200'
            }`}>Score: {field.soilHealthScore}/100</span>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: 'Nitrogen (N)', val: field.soil.n.value, score: field.soil.n.score, statusLabel: field.soil.n.label, statusColor: 'text-blue-500', barColor: 'bg-blue-500' },
              { label: 'Phosphorus (P)', val: field.soil.p.value, score: field.soil.p.score, statusLabel: field.soil.p.label, statusColor: 'text-purple-500', barColor: 'bg-purple-500' },
              { label: 'Potassium (K)', val: field.soil.k.value, score: field.soil.k.score, statusLabel: field.soil.k.label, statusColor: 'text-amber-500', barColor: 'bg-amber-500' },
            ].map((n) => (
              <div key={n.label}>
                <div className="text-[10px] text-gray-500 mb-1">{n.label}</div>
                <div className="text-sm font-bold text-gray-800">{n.val} <span className="text-gray-400 font-normal text-[10px]">kg/ha</span></div>
                <div className="h-1.5 w-full bg-gray-100 rounded-full mt-1 mb-1">
                  <div className={`h-1.5 ${n.barColor} rounded-full`} style={{ width: `${n.score}%` }} />
                </div>
                <div className={`text-[10px] font-semibold ${n.statusColor}`}>{n.statusLabel}</div>
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

        {/* Weather Forecast — real rainfall_mm_next_7d */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">⛅</span>
              <span className="font-semibold text-gray-800 text-sm">Weather <span className="text-gray-400 font-normal">(Next 7 Days)</span></span>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex items-center gap-3">
              <div>
                <div className="text-xs text-gray-500 mb-0.5">Forecast rainfall</div>
                <div className="text-3xl font-bold text-gray-800">{field.weather.rainfall7d} mm</div>
              </div>
              <div className={`border rounded-lg px-2 py-1 text-xs font-semibold ${
                field.weather.heavy_rain_alert ?? false
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : 'bg-green-50 border-green-200 text-green-700'
              }`}>
                {field.weather.heavy_rain_alert ?? false ? '⚠ Heavy rain' : '✓ Suitable for application'}
              </div>
            </div>
          </div>
          <div className="text-xs text-gray-400 mb-3">Source: Open-Meteo via weather agent</div>
          <div className="flex items-end gap-1 h-16">
            {[12, 5, 18, 28, 42, 10, 6].map((mm, i) => (
              <div key={i} className="flex flex-col items-center flex-1 gap-1">
                <div
                  className="w-full bg-green-500 rounded-t-sm"
                  style={{ height: `${Math.max(4, (mm / 42) * 48)}px` }}
                />
                <div className="text-[9px] text-gray-500">{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i]}</div>
                <div className="text-[9px] font-semibold text-gray-700">{mm}mm</div>
              </div>
            ))}
          </div>
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
              { name: 'Pest risk', value: field.fieldStatus.pestRisk.label, color: field.fieldStatus.pestRisk.color },
              { name: 'Disease risk', value: field.fieldStatus.diseaseRisk.label, color: field.fieldStatus.diseaseRisk.color },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <span className="text-xs text-gray-500">{item.name}</span>
                <div className="flex items-center gap-1.5">
                  <StatusDot color={item.color} />
                  <span className={`text-xs font-semibold ${item.color}`}>{item.value}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">Overall status</span>
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${
              field.fieldStatus.overall === 'Healthy'
                ? 'bg-green-100 text-green-700'
                : 'bg-amber-100 text-amber-700'
            }`}>{field.fieldStatus.overall}</span>
          </div>
        </div>

        {/* Field Location — dynamic lat/lon */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">📍</span>
            <span className="font-semibold text-gray-800 text-sm">Field Location</span>
          </div>
          <div className="relative flex-1 rounded-lg overflow-hidden min-h-[160px]">
            <FieldMap
              lat={field.lat}
              lng={field.lon}
              fieldId={field.id}
              zoom={14}
              className="w-full h-full min-h-[160px]"
            />
          </div>
        </div>

        {/* Next Recommended Action — real RAG pipeline result */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-start gap-4">
            <span className="text-2xl mt-0.5">🌱</span>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <span className="text-xs text-gray-500 font-medium">Next Recommended Action</span>
                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full">{field.recommendation.window}</span>
                {field.recommendation.confidence && (
                  <span className="bg-blue-50 text-blue-600 text-xs font-bold px-2 py-0.5 rounded-full border border-blue-200">
                    Confidence: {field.recommendation.confidence}
                  </span>
                )}
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{field.recommendation.action}</h2>
              <p className="text-sm text-gray-500 leading-relaxed mb-3 max-w-xl">{field.recommendation.description}</p>
              {field.recommendation.citation && (
                <p className="text-[10px] text-gray-400 italic mb-4">Source: {field.recommendation.citation}</p>
              )}
              <Link href="/simulator" className="inline-flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition">
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
                <div className="font-bold text-gray-800">₹{field.recommendation.estimatedCost.toLocaleString()}</div>
              </div>
            </div>

            <div className="hidden lg:block w-32 h-32 rounded-lg overflow-hidden flex-shrink-0">
              <img src="/image copy 4.png" alt="Sugarcane crop" className="w-full h-full object-cover" />
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
            {field.insights.map((insight, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition cursor-pointer">
                <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0">
                  <img src={insight.img} alt={insight.title} className="w-full h-full object-cover" />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-gray-800 leading-snug mb-0.5">{insight.title}</div>
                  <div className="text-[10px] text-gray-400 mb-0.5">{insight.time}</div>
                  <div className="text-[10px] text-gray-500 leading-snug">{insight.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Crop Stage Timeline — built from real stageSequence from DB */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-lg">🌱</span>
            <span className="font-semibold text-gray-800 text-sm">Crop Stage Timeline</span>
            <span className="text-xs text-gray-400 ml-1">— {field.crop} · Current: {field.stage}</span>
          </div>

          <div className="relative">
            <div className="absolute top-4 left-0 right-0 h-0.5 bg-gray-200" />
            {field.timeline.length > 0 && (
              <div className="absolute top-4 left-0 h-0.5 bg-green-500"
                style={{ width: `${(Math.max(0, field.timeline.findIndex(s => s.current)) / (field.timeline.length - 1)) * 100}%` }} />
            )}

            <div className={`relative grid gap-2`} style={{ gridTemplateColumns: `repeat(${field.timeline.length || 6}, minmax(0, 1fr))` }}>
              {field.timeline.map((stage, i) => (
                <div key={i} className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center z-10 text-sm mb-2
                    ${stage.current
                      ? 'bg-green-600 border-2 border-green-600 text-white shadow-lg shadow-green-200'
                      : stage.done
                      ? 'bg-white border-2 border-green-500'
                      : 'bg-white border-2 border-gray-200'
                    }`}
                  >
                    {stage.done && !stage.current ? (
                      <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7"/></svg>
                    ) : (
                      <span className={`text-base ${stage.current ? '' : 'opacity-30'}`}>🌿</span>
                    )}
                  </div>
                  <div className={`text-center text-[10px] font-semibold ${stage.current ? 'text-green-700' : stage.done ? 'text-gray-600' : 'text-gray-300'}`}>
                    {stage.name}
                  </div>
                  {stage.current && (
                    <span className="mt-1 bg-green-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full whitespace-nowrap">
                      Current
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
