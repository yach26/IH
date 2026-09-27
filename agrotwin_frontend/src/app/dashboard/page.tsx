"use client";

import React from 'react';
import dynamic from 'next/dynamic';

const FieldMap = dynamic(() => import('@/components/ui/FieldMap'), { ssr: false });
import Link from 'next/link';

// ─── Mock Data Template ────────────────────────────────────────────────────────
const defaultField = {
  id: 'A-104',
  status: 'Active',
  location: 'Kolhapur, Maharashtra',
  crop: 'Rice (Kharif 2025)',
  stage: 'Tillering Stage',
  stageDay: 28,
  area: '2.5 ha',
  soilType: 'Clay Loam',
  weather: { temp: 28, condition: 'Partly cloudy', humidity: 78, wind: 12, rain24h: 0 },
  soil: {
    n: { value: 72, label: 'Moderate', color: 'bg-blue-500' },
    p: { value: 55, label: 'Low', color: 'bg-purple-500' },
    k: { value: 65, label: 'Moderate', color: 'bg-amber-500' },
    note: 'Nitrogen levels are moderate. Consider urea application within 3 days for optimal tillering.',
  },
  forecast: [
    { day: 'Mon', mm: 12 }, { day: 'Tue', mm: 5 }, { day: 'Wed', mm: 18 },
    { day: 'Thu', mm: 28 }, { day: 'Fri', mm: 42 }, { day: 'Sat', mm: 10 }, { day: 'Sun', mm: 6 },
  ],
  fieldStatus: {
    cropCondition: { label: 'Good', color: 'text-green-500' },
    waterStress: { label: 'Low', color: 'text-gray-400' },
    pestRisk: { label: 'Moderate', color: 'text-amber-500' },
    diseaseRisk: { label: 'Low', color: 'text-gray-400' },
    overall: 'Healthy',
  },
  recommendation: {
    action: 'Apply Urea (46-0-0)',
    window: 'Within 3 days',
    description: 'Based on current soil nitrogen levels and tillering stage, apply 50 kg/ha of urea. This will support tiller development and improve leaf colour.',
    quantity: '50 kg/ha',
    applicationWindow: 'Next 3 days',
    expectedBenefit: 'Increased tiller count and greener leaves',
  },
  timeline: [
    { name: 'Sowing', day: 0, done: true },
    { name: 'Germination', day: 7, done: true },
    { name: 'Seedling', day: 14, done: true },
    { name: 'Tillering', day: 28, current: true },
    { name: 'Panicle Initiation', day: 50, done: false },
    { name: 'Flowering', day: 70, done: false },
    { name: 'Maturity', day: 100, done: false },
  ],
  insights: [
    { title: 'Rainfall forecast updated', time: '2 hours ago', desc: 'Higher rainfall likely in next 5 days.', img: '/image copy 2.png' },
    { title: 'Nitrogen level lower than optimal', time: '1 day ago', desc: 'Consider urea application.', img: '/image copy 3.png' },
    { title: 'Pest risk moderate', time: '2 days ago', desc: 'Monitor for yellow stem borer.', img: '/image copy 4.png' },
  ],
};

// ─── Sub-components ───────────────────────────────────────────────────────────

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
  const [field, setField] = React.useState(defaultField);
  const maxForecastMm = Math.max(...field.forecast.map(d => d.mm));

  React.useEffect(() => {
    fetch('http://localhost:8000/fields/SYN-001/twin')
      .then(r => r.json())
      .then(data => {
        setField(prev => ({
          ...prev,
          id: data.fieldId || prev.id,
          crop: data.crop || prev.crop,
          stage: data.growthStage || prev.stage,
          soil: {
            ...prev.soil,
            n: { ...prev.soil.n, value: data.nutrients?.n?.current ?? prev.soil.n.value },
            p: { ...prev.soil.p, value: data.nutrients?.p?.current ?? prev.soil.p.value },
            k: { ...prev.soil.k, value: data.nutrients?.k?.current ?? prev.soil.k.value },
          },
          recommendation: {
            ...prev.recommendation,
            action: data.currentPlan?.nextAction || prev.recommendation.action,
            quantity: data.currentPlan?.quantity || prev.recommendation.quantity,
            applicationWindow: data.currentPlan?.applicationWindow || prev.recommendation.applicationWindow,
          },
          insights: data.activeAlert ? [
            {
              title: data.activeAlert.title,
              time: 'Just now',
              desc: data.activeAlert.description,
              img: '/image copy 2.png'
            },
            ...prev.insights
          ] : prev.insights
        }));
      })
      .catch(err => console.error("Error fetching twin data:", err));
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
        {/* dark gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />

        {/* Field overview label */}
        <div className="absolute top-4 left-5 flex items-center gap-2 text-white/80 text-xs font-semibold uppercase tracking-widest">
          <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2z"/></svg>
          Field Overview
        </div>

        {/* View on Map */}
        <button className="absolute top-4 right-5 flex items-center gap-1.5 bg-white/90 text-gray-800 text-xs font-semibold px-3 py-1.5 rounded-full shadow hover:bg-white transition">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          View on Map
        </button>

        {/* Field Title */}
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
            { icon: '📅', label: 'Current Stage', value: `${field.stage}\nDay ${field.stageDay}` },
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

        {/* Weather widget */}
        <div className="absolute bottom-4 right-5 hidden md:flex items-center gap-4 bg-white/15 backdrop-blur-md border border-white/20 rounded-xl px-5 py-3">
          <div>
            <div className="text-white text-3xl font-bold">{field.weather.temp}°C</div>
            <div className="text-white/70 text-xs">{field.weather.condition}</div>
          </div>
          <div className="text-white/80 text-xs space-y-1">
            <div className="flex justify-between gap-6"><span>Humidity</span><span className="font-semibold text-white">{field.weather.humidity}%</span></div>
            <div className="flex justify-between gap-6"><span>Wind</span><span className="font-semibold text-white">{field.weather.wind} km/h</span></div>
            <div className="flex justify-between gap-6"><span>Rain (24h)</span><span className="font-semibold text-white">{field.weather.rain24h} mm</span></div>
          </div>
        </div>
      </div>

      {/* ── Main Grid ── */}
      <div className="p-4 md:p-6 grid grid-cols-1 lg:grid-cols-4 gap-4">

        {/* ── Row 1: Soil | Weather | Field Status | Location ── */}

        {/* Soil Health */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">🌱</span>
              <span className="font-semibold text-gray-800 text-sm">Soil Health</span>
            </div>
            <span className="text-xs font-semibold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">Moderate</span>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: 'Nitrogen (N)', val: field.soil.n.value, statusLabel: field.soil.n.label, statusColor: 'text-blue-500', barColor: 'bg-blue-500' },
              { label: 'Phosphorus (P)', val: field.soil.p.value, statusLabel: field.soil.p.label, statusColor: 'text-purple-500', barColor: 'bg-purple-500' },
              { label: 'Potassium (K)', val: field.soil.k.value, statusLabel: field.soil.k.label, statusColor: 'text-amber-500', barColor: 'bg-amber-500' },
            ].map((n) => (
              <div key={n.label}>
                <div className="text-[10px] text-gray-500 mb-1">{n.label}</div>
                <div className="text-sm font-bold text-gray-800">{n.val} <span className="text-gray-400 font-normal">/ 100</span></div>
                <div className="h-1.5 w-full bg-gray-100 rounded-full mt-1 mb-1">
                  <div className={`h-1.5 ${n.barColor} rounded-full`} style={{ width: `${n.val}%` }} />
                </div>
                <div className={`text-[10px] font-semibold ${n.statusColor}`}>{n.statusLabel}</div>
              </div>
            ))}
          </div>

          <div className="flex items-start gap-2 bg-green-50 rounded-lg p-3 text-xs text-gray-600 leading-relaxed">
            <span className="text-green-600 mt-0.5">🌿</span>
            <span>{field.soil.note}</span>
          </div>
        </div>

        {/* Weather Forecast */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">⛅</span>
              <span className="font-semibold text-gray-800 text-sm">Weather Forecast <span className="text-gray-400 font-normal">(Next 7 Days)</span></span>
            </div>
          </div>

          <div className="mb-4">
            <div className="flex items-center gap-3">
              <div>
                <div className="text-xs text-gray-500 mb-0.5">Likely rainfall</div>
                <div className="text-3xl font-bold text-gray-800">42 mm</div>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg px-2 py-1 text-xs text-green-700 font-semibold">
                ↑ +20% higher<br/>than last week
              </div>
            </div>
          </div>

          <div className="flex items-end gap-1 h-16">
            {field.forecast.map((d) => (
              <div key={d.day} className="flex flex-col items-center flex-1 gap-1">
                <div
                  className="w-full bg-green-500 rounded-t-sm"
                  style={{ height: `${Math.max(4, (d.mm / maxForecastMm) * 48)}px` }}
                />
                <div className="text-[9px] text-gray-500">{d.day}</div>
                <div className="text-[9px] font-semibold text-gray-700">{d.mm}mm</div>
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
            <span className="bg-green-100 text-green-700 text-xs font-bold px-3 py-1 rounded-full">Healthy</span>
          </div>
        </div>

        {/* Field Location */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex flex-col">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">📍</span>
            <span className="font-semibold text-gray-800 text-sm">Field Location</span>
          </div>
          <div className="relative flex-1 rounded-lg overflow-hidden min-h-[160px]">
            <FieldMap
              lat={16.705}
              lng={74.2433}
              fieldId={field.id}
              zoom={14}
              className="w-full h-full min-h-[160px]"
            />
          </div>
        </div>

        {/* ── Row 2: Recommendation (wide) | Insights (right) ── */}

        {/* Next Recommended Action */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-start gap-4">
            <span className="text-2xl mt-0.5">🌱</span>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <span className="text-xs text-gray-500 font-medium">Next Recommended Action</span>
                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full">{field.recommendation.window}</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{field.recommendation.action}</h2>
              <p className="text-sm text-gray-500 leading-relaxed mb-5 max-w-xl">{field.recommendation.description}</p>
              <Link href="/simulator" className="inline-flex items-center gap-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition">
                View Detailed Plan
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
              </Link>
            </div>

            {/* Stats */}
            <div className="hidden md:flex flex-col gap-4 min-w-[160px] text-sm">
              <div>
                <div className="flex items-center gap-2 text-gray-400 text-xs mb-0.5">
                  <span>📦</span> Quantity
                </div>
                <div className="font-bold text-gray-800">{field.recommendation.quantity}</div>
              </div>
              <div>
                <div className="flex items-center gap-2 text-gray-400 text-xs mb-0.5">
                  <span>📅</span> Application window
                </div>
                <div className="font-bold text-gray-800">{field.recommendation.applicationWindow}</div>
              </div>
              <div>
                <div className="flex items-center gap-2 text-gray-400 text-xs mb-0.5">
                  <span>🎯</span> Expected benefit
                </div>
                <div className="font-bold text-gray-800">{field.recommendation.expectedBenefit}</div>
              </div>
            </div>

            {/* Rice image */}
            <div className="hidden lg:block w-32 h-32 rounded-lg overflow-hidden flex-shrink-0">
              <img src="/image copy 4.png" alt="Rice crop" className="w-full h-full object-cover" />
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
            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/></svg>
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

          <div className="mt-4 pt-3 border-t border-gray-100">
            <button className="flex items-center gap-2 text-xs font-semibold text-green-700 hover:text-green-900 transition">
              View All Insights
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
            </button>
          </div>
        </div>

        {/* ── Row 3: Crop Stage Timeline ── */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-lg">🌱</span>
            <span className="font-semibold text-gray-800 text-sm">Crop Stage Timeline</span>
          </div>

          <div className="relative">
            {/* Connecting line */}
            <div className="absolute top-4 left-0 right-0 h-0.5 bg-gray-200" />
            <div className="absolute top-4 left-0 h-0.5 bg-green-500" style={{ width: `${(3 / (field.timeline.length - 1)) * 100}%` }} />

            <div className="relative grid grid-cols-7 gap-2">
              {field.timeline.map((stage, i) => (
                <div key={i} className="flex flex-col items-center">
                  {/* Stage icon / dot */}
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
                  <div className={`text-[9px] ${stage.current ? 'text-green-500' : 'text-gray-300'}`}>
                    Day {stage.day}
                  </div>
                  {stage.current && (
                    <span className="mt-1 bg-green-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full whitespace-nowrap">
                      Current Stage
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
