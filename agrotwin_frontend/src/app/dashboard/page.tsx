"use client";

import React, { Suspense } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import {
  getTwin, recommend, overridePlan, getRecommendationHistory, ApiError,
  type TwinResponse, type RecommendationHistoryEntry,
} from '@/lib/api';
import { useFieldParam } from '@/lib/useFieldParam';
import FieldSelector from '@/components/ui/FieldSelector';
import FieldOnboarding from '@/components/ui/FieldOnboarding';
import StageTimeline from '@/components/ui/StageTimeline';
import { Volume2, History, ShieldCheck } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

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

function formatFertilizerName(key: string): string {
  return key.replace(/_kg_ha$/i, '').replace(/_/g, ' ');
}

// FieldState stores these as fixed English codes (used in equality checks
// throughout this file) — translation only happens at render time via this
// lookup, so switching language never risks breaking the underlying logic.
function tStatus(t: (key: string) => string, label: string): string {
  const map: Record<string, string> = {
    'High': 'dash.high', 'Moderate': 'dash.moderate', 'Low': 'dash.low',
    'Not available': 'dash.notAvailable', 'Good': 'dash.good',
    'Healthy': 'dash.healthy', 'Needs Attention': 'dash.needsAttention', 'Unknown': 'dash.unknown',
  };
  const key = map[label];
  return key ? t(key) : label;
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
    fertilizerBreakdown: Record<string, number>;
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
  // Citation is shown once as its own footer line (below) — keep it out of
  // this paragraph so the two don't repeat the same source twice.
  const description = `Based on real soil test (N=${nutrients.n?.current ?? '—'} kg/ha, P=${nutrients.p?.current ?? '—'} kg/ha, K=${nutrients.k?.current ?? '—'} kg/ha) and ${data.crop} at ${currentStageName} stage. Nutrient gaps: N ${gap.N ?? '—'} kg/ha, P₂O₅ ${gap.P2O5 ?? '—'} kg/ha, K₂O ${gap.K2O ?? '—'} kg/ha.`;

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
      fertilizerBreakdown: plan.fertilizerBreakdown || {},
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

// ─── Official Recommendation Panel — the hero of the page ─────────────────────
function OfficialRecommendationPanel({
  field,
  generating,
  generateError,
  onGenerate,
}: {
  field: FieldState;
  generating: boolean;
  generateError: string | null;
  onGenerate: () => void;
}) {
  const { t, language } = useLanguage();
  const rec = field.recommendation;
  const [doneSteps, setDoneSteps] = React.useState<Set<number>>(new Set());
  const toggleStep = (i: number) =>
    setDoneSteps((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i); else next.add(i);
      return next;
    });

  function handlePrint() {
    window.print();
  }

  // Built only from real fields already on the recommendation — no invented
  // thresholds. The final "re-check" step is a generic engineering-default
  // prompt (not a sourced re-testing interval), labelled as such.
  const steps: string[] = [
    `${t('dash.applyAction')} ${rec.action} ${language === 'en' ? 'within' : ''}: ${rec.applicationWindow}`,
    ...rec.requiredActions,
    'Re-run the recommendation after this crop\'s next growth-stage change, a new soil test, or a significant weather event (ENGINEERING_DEFAULT — no sourced re-testing interval).',
  ];

  const [speaking, setSpeaking] = React.useState(false);
  const [voiceUnavailable, setVoiceUnavailable] = React.useState(false);
  const voiceLangMap: Record<string, string> = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN' };

  function handleListen() {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    // A full farm-status narration, not just the one-line recommendation:
    // soil health, each nutrient's status, weather, the recommendation
    // itself, and every next step — all built from data already on screen,
    // with fixed phrases translated via t() and only the backend-generated
    // parts (crop/product names, numbers, dates, citations) left in English
    // since they were never machine-translated in the first place.
    const parts: string[] = [
      `${t('dash.listenFullSummary')} ${field.id}.`,
    ];
    if (field.soilHealthScore != null) {
      parts.push(`${t('dash.listenSoilScore')}: ${field.soilHealthScore} ${t('dash.listenOutOf100')}.`);
      parts.push(`${t('dash.listenNutrients')} ${tStatus(t, field.soil.n.label)}. ${t('dash.listenPhosphorusIs')} ${tStatus(t, field.soil.p.label)}. ${t('dash.listenPotassiumIs')} ${tStatus(t, field.soil.k.label)}.`);
    }
    if (field.weather.available) {
      parts.push(`${t('dash.listenWeatherIs')} ${field.weather.rainfall7d} mm.`);
    } else {
      parts.push(t('dash.listenWeatherNone'));
    }
    if (!isAbstain && !isNoData) {
      parts.push(`${t('dash.applyAction')}: ${rec.action}.`);
      parts.push(`${t('dash.quantity')}: ${rec.quantity}.`);
      parts.push(`${t('dash.confidence')}: ${rec.confidence}.`);
      parts.push(t('dash.listenStepsIntro'));
      steps.forEach((s, i) => parts.push(`${i + 1}. ${s}`));
    } else if (rec.reason) {
      parts.push(`${t('dash.note')}: ${rec.reason}`);
    }
    const utterance = new SpeechSynthesisUtterance(parts.filter(Boolean).join(" "));
    const targetLang = voiceLangMap[language] || 'en-IN';
    utterance.lang = targetLang;
    // Not every browser ships an installed Hindi/Marathi voice — pick the
    // closest available match rather than silently falling back to a
    // default English voice while claiming lang="hi-IN".
    const voices = window.speechSynthesis.getVoices();
    const match = voices.find((v) => v.lang === targetLang) || voices.find((v) => v.lang.startsWith(targetLang.slice(0, 2)));
    setVoiceUnavailable(language !== 'en' && !match);
    if (match) utterance.voice = match;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
    setSpeaking(true);
  }

  const isAbstain = rec.status === 'ABSTAIN';
  const isNoData = rec.status === 'NO_DATA';
  const fertilizerEntries = Object.entries(rec.fertilizerBreakdown).filter(([, v]) => v > 0);

  return (
    <div id="official-recommendation" className="relative gov-panel bg-surface border-2 border-primary/20 shadow-sm mx-4 md:mx-6 mt-4 p-5 md:p-7">
      {/* Stamp-style confidence badge */}
      {!isAbstain && !isNoData && rec.confidence && (
        <div
          className={`absolute top-3 right-3 md:top-5 md:right-6 border-2 rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider -rotate-6 select-none ${confidenceBadgeClass(rec.confidence)}`}
          style={{ borderStyle: 'double', borderWidth: '3px' }}
        >
          {t('dash.confidence')}<br />{rec.confidence}
        </div>
      )}

      <div className="flex items-center justify-between gap-3 mb-1 no-print">
        <span className="text-xs font-bold uppercase tracking-widest text-primary">
          {t('dash.officialRecommendation')}
        </span>
      </div>
      <h1 className="font-serif text-xl md:text-2xl font-bold text-foreground mb-4 pr-28">
        {t('dash.fertilizerPlanFor')} {field.id}
      </h1>

      {isAbstain ? (
        <div className="border-l-4 border-red-600 bg-red-50 p-4">
          <p className="text-xs font-bold text-red-700 uppercase tracking-wide mb-1">{t('dash.abstainedBadge')}</p>
          <p className="text-base font-semibold text-foreground mb-2">{t('dash.abstainedTitle')}</p>
          {rec.reason && <p className="text-sm text-muted mb-2">{rec.reason}</p>}
          {rec.requiredActions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted mb-1">{t('dash.requiredBeforePlan')}</p>
              <ul className="text-sm text-foreground list-disc list-inside space-y-0.5">
                {rec.requiredActions.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}
        </div>
      ) : isNoData ? (
        <div className="border-l-4 border-muted bg-surface-hover p-4">
          <p className="text-base font-semibold text-foreground mb-1">{t('dash.noRecGenerated')}</p>
          <p className="text-sm text-muted mb-3">{t('dash.runPipeline')}</p>
          {generateError && <p className="text-sm text-red-600 mb-3">{generateError}</p>}
          <button
            onClick={onGenerate}
            disabled={generating}
            className="inline-flex items-center gap-2 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 gov-panel transition"
          >
            {generating ? t('dash.generating') : t('dash.generateRecommendation')}
          </button>
        </div>
      ) : (
        <>
          {/* Big fertilizer quantity cards */}
          {fertilizerEntries.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-5">
              {fertilizerEntries.map(([key, val]) => (
                <div key={key} className="gov-panel border border-border bg-surface-hover px-4 py-3 text-center">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-muted mb-1">{formatFertilizerName(key)}</div>
                  <div className="text-3xl md:text-4xl font-extrabold text-primary font-serif leading-none">{val}</div>
                  <div className="text-[11px] text-muted mt-1">kg/ha</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted mb-5">{rec.quantity}</p>
          )}

          <p className="text-sm text-muted leading-relaxed mb-5 max-w-2xl">{rec.description}</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Next steps checklist */}
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-foreground mb-2">{t('dash.nextSteps')}</p>
              <ol className="space-y-2">
                {steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <button
                      onClick={() => toggleStep(i)}
                      aria-pressed={doneSteps.has(i)}
                      className={`no-print mt-0.5 flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center text-[10px] font-bold transition ${
                        doneSteps.has(i)
                          ? 'bg-primary border-primary text-white'
                          : 'border-muted text-muted'
                      }`}
                    >
                      {doneSteps.has(i) ? '✓' : i + 1}
                    </button>
                    <span className={`text-sm ${doneSteps.has(i) ? 'line-through text-muted' : 'text-foreground'}`}>{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* Reasons / evidence */}
            <div className="text-sm">
              {(rec.confidence === 'LOW' || rec.confidence === 'MEDIUM') && rec.flags.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-accent mb-1.5">{t('dash.reducedConfidence')}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {rec.flags.map((flag, i) => {
                      const label = flag.split(/[:(]/, 1)[0].trim().replace(/_/g, ' ');
                      return (
                        <span key={i} title={flag} className="text-[11px] font-medium text-accent bg-accent-bg border border-accent/30 rounded-full px-2 py-0.5 cursor-help">
                          {label}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
              {rec.estimatedCost != null && (
                <div className="mb-2">
                  <span className="text-xs text-muted">{t('dash.estCost')}: </span>
                  <span className="font-bold text-foreground">₹{Math.round(rec.estimatedCost).toLocaleString()}</span>
                  {rec.costCitation && <span className="block text-[10px] text-muted mt-0.5">{t('dash.engineeringEstimate')}</span>}
                </div>
              )}
              {rec.citation && (
                <p className="text-[11px] text-muted italic">{t('dash.source')}: {rec.citation}</p>
              )}
              {voiceUnavailable && (
                <p className="text-[10px] text-accent mt-1">
                  {language === 'hi' ? 'इस ब्राउज़र में हिंदी आवाज़ उपलब्ध नहीं — डिफ़ॉल्ट आवाज़ में सुना जाएगा।' : 'या ब्राउझरमध्ये मराठी आवाज उपलब्ध नाही — डीफॉल्ट आवाजात ऐकवले जाईल.'}
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 mt-6 no-print">
            <Link href={`/simulator?field=${encodeURIComponent(field.id)}`} className="inline-flex items-center gap-2 bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-5 py-2.5 gov-panel transition">
              {t('dash.simulateInWhatIf')}
            </Link>
            <button onClick={handlePrint} className="inline-flex items-center gap-2 border border-border hover:border-primary text-foreground text-sm font-semibold px-5 py-2.5 gov-panel transition">
              {t('dash.downloadPrint')}
            </button>
            <button
              onClick={handleListen}
              className={`inline-flex items-center gap-2 border text-sm font-semibold px-5 py-2.5 gov-panel transition ${
                speaking ? "border-primary bg-primary/10 text-primary animate-pulse" : "border-border hover:border-primary text-foreground"
              }`}
            >
              <Volume2 className="w-4 h-4" />
              {speaking ? t('dash.stop') : t('dash.listen')}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Recommendation History & Agronomist Oversight ────────────────────────────
// Surfaces two real backend capabilities that already existed but were never
// exposed in the frontend: GET /fields/{id}/recommendations (every past
// recommendation, incl. superseded ones) and POST /fields/{id}/override
// (agronomist override, already implemented server-side with its own audit
// logging — see routes.py agronomist_override()).
function statusBadgeClass(status: string): string {
  if (status === 'SUPERSEDED') return 'bg-surface-hover text-muted border-border';
  if (status === 'ABSTAINED') return 'bg-red-50 text-red-700 border-red-200';
  if (status === 'NO_FERTILIZER_NEEDED') return 'bg-green-50 text-green-700 border-green-200';
  return 'bg-primary/10 text-primary border-primary/30';
}

function OverrideForm({
  fieldId,
  recommendationId,
  currentPlan,
  onDone,
  onCancel,
}: {
  fieldId: string;
  recommendationId: number;
  currentPlan: Record<string, number>;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [values, setValues] = React.useState<Record<string, string>>(
    Object.fromEntries(Object.entries(currentPlan).map(([k, v]) => [k, String(v)]))
  );
  const [reason, setReason] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  function handleSubmit() {
    if (!reason.trim()) {
      setError('A reason is required for an agronomist override.');
      return;
    }
    setSubmitting(true);
    setError(null);
    const new_plan: Record<string, number> = {};
    for (const [k, v] of Object.entries(values)) {
      const n = Number(v);
      if (Number.isFinite(n)) new_plan[k] = n;
    }
    overridePlan(fieldId, { recommendation_id: recommendationId, new_plan, reason: reason.trim() })
      .then(() => { setSubmitting(false); onDone(); })
      .catch((err) => { setSubmitting(false); setError(err instanceof ApiError ? err.message : 'Override failed.'); });
  }

  return (
    <div className="mt-3 gov-panel border border-primary/30 bg-primary/5 p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-primary mb-3">Agronomist Override</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
        {Object.entries(values).map(([key, val]) => (
          <div key={key}>
            <label className="block text-[10px] font-semibold text-muted mb-1">{formatFertilizerName(key)}</label>
            <input
              type="number"
              step="any"
              value={val}
              onChange={(e) => setValues((v) => ({ ...v, [key]: e.target.value }))}
              className="w-full text-sm border border-border gov-panel px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        ))}
      </div>
      <label className="block text-[10px] font-semibold text-muted mb-1">Reason for override (required)</label>
      <textarea
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        rows={2}
        placeholder="e.g. Farmer reports visible K deficiency symptoms not captured by the soil test."
        className="w-full text-sm border border-border gov-panel px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary mb-3"
      />
      {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="bg-primary hover:bg-primary-hover disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 gov-panel transition"
        >
          {submitting ? 'Submitting…' : 'Submit Override'}
        </button>
        <button onClick={onCancel} className="text-xs font-semibold text-muted hover:text-foreground px-4 py-2">
          Cancel
        </button>
      </div>
    </div>
  );
}

function HistoryOversightPanel({ fieldId, onOverridden }: { fieldId: string; onOverridden: () => void }) {
  const [history, setHistory] = React.useState<RecommendationHistoryEntry[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [expanded, setExpanded] = React.useState(false);
  const [overridingId, setOverridingId] = React.useState<number | null>(null);

  const fetchHistory = React.useCallback(() => {
    getRecommendationHistory(fieldId)
      .then((data) => { setHistory(data.history); setError(null); })
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load recommendation history.'));
  }, [fieldId]);

  React.useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const visible = expanded ? history : history?.slice(0, 3);
  const latest = history?.[0];

  return (
    <div className="lg:col-span-3 bg-surface gov-panel border border-border shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-primary" />
          <span className="font-semibold text-foreground text-sm">Recommendation History &amp; Oversight</span>
        </div>
        {latest && latest.status !== 'SUPERSEDED' && overridingId !== latest.recommendation_id && (
          <button
            onClick={() => setOverridingId(latest.recommendation_id)}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
          >
            <ShieldCheck className="w-3.5 h-3.5" /> Override latest plan
          </button>
        )}
      </div>

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
      {history === null && !error && <p className="text-sm text-muted">Loading history…</p>}
      {history !== null && history.length === 0 && <p className="text-sm text-muted italic">No recommendations generated yet for this field.</p>}

      {latest && overridingId === latest.recommendation_id && (
        <OverrideForm
          fieldId={fieldId}
          recommendationId={latest.recommendation_id}
          currentPlan={latest.how_much || {}}
          onCancel={() => setOverridingId(null)}
          onDone={() => { setOverridingId(null); fetchHistory(); onOverridden(); }}
        />
      )}

      <div className="mt-4 space-y-2">
        {(visible || []).map((h) => (
          <div key={h.recommendation_id} className="flex items-start gap-3 py-2 border-b border-border last:border-0">
            <span className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full border flex-shrink-0 ${statusBadgeClass(h.status)}`}>
              {h.status.replace(/_/g, ' ')}
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-foreground font-medium">
                {h.what || '—'}
                {h.confidence && <span className="text-muted font-normal"> · Confidence: {h.confidence}</span>}
              </div>
              <div className="text-[11px] text-muted">{h.generated_at}</div>
              {h.confidence_reason === 'Agronomist Override' && (
                <div className="text-[11px] text-primary font-medium mt-0.5">Manually overridden by an agronomist</div>
              )}
              {h.superseded_by && <div className="text-[11px] text-muted">Superseded by recommendation #{h.superseded_by}</div>}
            </div>
          </div>
        ))}
      </div>

      {history && history.length > 3 && (
        <button onClick={() => setExpanded((e) => !e)} className="mt-3 text-xs font-semibold text-primary hover:underline">
          {expanded ? 'Show less' : `Show all ${history.length} entries`}
        </button>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
function DashboardField() {
  const { t } = useLanguage();
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
      <div className="min-h-screen bg-background font-sans flex items-center justify-center p-6">
        <div className="max-w-md text-center bg-surface gov-panel border border-red-200 shadow-sm p-8">
          <div className="text-3xl mb-3">⚠️</div>
          <h2 className="font-serif text-lg font-bold text-foreground mb-2">{t('dash.cantReachBackend')}</h2>
          <p className="text-sm text-muted mb-4">{error}</p>
          <button
            onClick={() => fetchTwin()}
            className="bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-5 py-2.5 gov-panel transition"
          >
            {t('dash.retry')}
          </button>
        </div>
      </div>
    );
  }

  if (loading && !field) {
    return (
      <div className="min-h-screen bg-background font-sans flex items-center justify-center">
        <div className="flex items-center gap-3 text-muted text-sm">
          <span className="inline-block w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
          {t('dash.loadingField')}
        </div>
      </div>
    );
  }

  if (!field) return null;

  return (
    <div className="min-h-screen bg-background font-sans">

      {error && (
        <div className="bg-red-50 border-b border-red-200 text-red-700 text-xs px-4 py-2 text-center">
          Connection to backend lost — showing last known data
          {lastUpdated && ` from ${lastUpdated.toLocaleTimeString()}`}.{' '}
          <button onClick={() => fetchTwin()} className="underline font-semibold">{t('dash.retry')}</button>
        </div>
      )}

      {/* ── Field selector bar ── */}
      <div className="bg-surface border-b border-border px-4 md:px-6 py-2.5 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted font-medium">{t('dash.field')}:</span>
          {fields.length > 0 ? (
            <FieldSelector fieldId={fieldId} fields={fields} onChange={setFieldId} />
          ) : (
            <span className="text-xs text-muted">{fieldsError ? `Field list unavailable (${fieldsError})` : 'Loading fields…'}</span>
          )}
        </div>
        <Link
          href={`/upload?field=${encodeURIComponent(fieldId)}`}
          className="inline-flex items-center gap-1.5 bg-primary hover:bg-primary-hover text-white text-xs font-semibold px-3 py-1.5 gov-panel transition"
        >
          📤 {t('dash.uploadSoilReport')}
        </Link>
      </div>

      {/* ── Gate: no soil report on file for this field yet ── */}
      {!field.hasSoilTest && (
        <div className="min-h-[70vh] flex items-center justify-center p-6">
          <div className="max-w-md text-center bg-surface gov-panel border border-border shadow-sm p-8">
            <div className="text-4xl mb-3">🧪</div>
            <h2 className="font-serif text-lg font-bold text-foreground mb-2">{t('dash.noSoilReport')} {field.id}</h2>
            <p className="text-sm text-muted mb-5">
              {t('dash.soilTestNeeded')}
            </p>
            <Link
              href={`/upload?field=${encodeURIComponent(field.id)}`}
              className="inline-flex items-center gap-2 bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-5 py-2.5 gov-panel transition"
            >
              📤 {t('dash.uploadSoilReport')}
            </Link>
          </div>
        </div>
      )}

      {/* ── Official Recommendation — the hero of the page ── */}
      {field.hasSoilTest && (
        <OfficialRecommendationPanel
          field={field}
          generating={generating}
          generateError={generateError}
          onGenerate={handleGenerateRecommendation}
        />
      )}

      {/* ── Field Overview Banner ── */}
      {field.hasSoilTest && (<>
      <div className="relative w-full h-56 md:h-72 overflow-hidden mt-4">
        <img
          src="/image.png"
          alt="Field overview"
          className="absolute inset-0 w-full h-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />

        <div className="absolute top-4 left-5 flex items-center gap-2 text-white/80 text-xs font-semibold uppercase tracking-widest">
          <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2z"/></svg>
          {t('dash.fieldOverview')}
        </div>

        <button
          onClick={scrollToMap}
          className="absolute top-4 right-5 flex items-center gap-1.5 bg-white/90 text-gray-800 text-xs font-semibold px-3 py-1.5 rounded-full shadow hover:bg-white transition"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          {t('dash.viewOnMap')}
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
            { icon: '🌾', label: t('dash.crop'), value: field.crop },
            { icon: '📅', label: t('dash.stage'), value: field.stage },
            { icon: '📐', label: t('dash.area'), value: field.area },
            { icon: '🪨', label: t('dash.soilType'), value: field.soilType || t('dash.notRecorded') },
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
            <div className="text-white/70 text-xs">{t('dash.weatherUnavailableShort')}</div>
          )}
        </div>
      </div>

      {/* ── Main Grid ── */}
      <div className="p-4 md:p-6 grid grid-cols-1 lg:grid-cols-4 gap-4">

        {/* Soil Health */}
        <div className="bg-surface gov-panel border border-border shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">🌱</span>
              <span className="font-semibold text-foreground text-sm">{t('dash.soilHealth')}</span>
            </div>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
              field.soilHealthScore == null ? 'text-gray-500 bg-gray-50 border-gray-200' :
              field.soilHealthScore >= 60 ? 'text-green-600 bg-green-50 border-green-200' :
              field.soilHealthScore >= 35 ? 'text-amber-600 bg-amber-50 border-amber-200' :
              'text-red-600 bg-red-50 border-red-200'
            }`}>{field.soilHealthScore == null ? t('dash.notAvailable') : `${field.soilHealthScore}/100`}</span>
          </div>

          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label: t('dash.nitrogen'), val: field.soil.n.value, score: field.soil.n.score, statusLabel: field.soil.n.label, statusColor: 'text-blue-500', barColor: 'bg-blue-500' },
              { label: t('dash.phosphorus'), val: field.soil.p.value, score: field.soil.p.score, statusLabel: field.soil.p.label, statusColor: 'text-purple-500', barColor: 'bg-purple-500' },
              { label: t('dash.potassium'), val: field.soil.k.value, score: field.soil.k.score, statusLabel: field.soil.k.label, statusColor: 'text-amber-500', barColor: 'bg-amber-500' },
            ].map((n) => (
              <div key={n.label}>
                <div className="text-[10px] text-gray-500 mb-1">{n.label}</div>
                <div className="text-sm font-bold text-gray-800">
                  {n.val ?? '—'} <span className="text-gray-400 font-normal text-[10px]">kg/ha</span>
                </div>
                <div className="h-1.5 w-full bg-gray-100 rounded-full mt-1 mb-1">
                  <div className={`h-1.5 ${n.barColor} rounded-full`} style={{ width: `${n.score ?? 0}%` }} />
                </div>
                <div className={`text-[10px] font-semibold ${n.score == null ? 'text-gray-400' : n.statusColor}`}>{tStatus(t, n.statusLabel)}</div>
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
        <div className="bg-surface gov-panel border border-border shadow-sm p-5">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">⛅</span>
              <span className="font-semibold text-foreground text-sm">{t('dash.weather7d')}</span>
            </div>
          </div>

          {field.weather.available ? (
            <>
              <div className="mb-4">
                <div className="flex items-center gap-3">
                  <div>
                    <div className="text-xs text-gray-500 mb-0.5">{t('dash.forecastRainfall')}</div>
                    <div className="text-3xl font-bold text-gray-800">{field.weather.rainfall7d} mm</div>
                  </div>
                  <div className={`border rounded-lg px-2 py-1 text-xs font-semibold ${
                    field.weather.heavy_rain_alert
                      ? 'bg-red-50 border-red-200 text-red-700'
                      : 'bg-green-50 border-green-200 text-green-700'
                  }`}>
                    {field.weather.heavy_rain_alert ? `⚠ ${t('dash.heavyRain')}` : `✓ ${t('dash.suitableForApplication')}`}
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-400">{t('dash.weatherSource')}</div>
              <div className="text-[10px] text-gray-300 mt-1">{t('dash.dailyBreakdownUnavailable')}</div>
            </>
          ) : (
            <div className="text-sm text-gray-400 italic py-4">
              {t('dash.weatherUnavailableField')}
            </div>
          )}
        </div>

        {/* Field Status — derived from real N sufficiency + weather_agent */}
        <div className="bg-surface gov-panel border border-border shadow-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">🌿</span>
            <span className="font-semibold text-foreground text-sm">{t('dash.fieldStatus')}</span>
          </div>

          <div className="space-y-3">
            {[
              { name: t('dash.cropCondition'), value: tStatus(t, field.fieldStatus.cropCondition.label), color: field.fieldStatus.cropCondition.color },
              { name: t('dash.waterStress'), value: tStatus(t, field.fieldStatus.waterStress.label), color: field.fieldStatus.waterStress.color },
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
              { name: t('dash.pestRisk') },
              { name: t('dash.diseaseRisk') },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <span className="text-xs text-gray-500">{item.name}</span>
                <span className="text-xs font-semibold text-gray-400">{t('dash.notAssessed')}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-gray-500">{t('dash.overallStatus')}</span>
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${
              field.fieldStatus.overall === 'Healthy'
                ? 'bg-green-100 text-green-700'
                : field.fieldStatus.overall === 'Unknown'
                ? 'bg-gray-100 text-gray-500'
                : 'bg-amber-100 text-amber-700'
            }`}>{tStatus(t, field.fieldStatus.overall)}</span>
          </div>
        </div>

        {/* Field Location — only rendered when the field has a real recorded lat/lon */}
        <div ref={mapCardRef} className="bg-surface gov-panel border border-border shadow-sm p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📍</span>
              <span className="font-semibold text-foreground text-sm">{t('dash.fieldLocation')}</span>
            </div>
            {field.lat != null && field.lon != null && (
              <a
                href={`https://www.google.com/maps?q=${field.lat},${field.lon}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] font-semibold text-gray-500 hover:text-green-700 transition underline"
              >
                {t('dash.openInGoogleMaps')}
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
              {t('dash.locationNotProvided')}
            </div>
          )}
        </div>

        {/* Recent Insights — real activeAlert only, honest empty state otherwise */}
        <div className="lg:row-span-2 bg-surface gov-panel border border-border shadow-sm p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-lg">💡</span>
              <span className="font-semibold text-foreground text-sm">{t('dash.recentInsights')}</span>
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
              <div className="text-xs text-gray-400 italic py-4 text-center">{t('dash.noRecentAlerts')}</div>
            )}
          </div>
        </div>

        {/* Crop Stage Timeline — shared component, read-only, built from real stageSequence */}
        <div className="lg:col-span-3 bg-surface gov-panel border border-border shadow-sm p-5">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-lg">🌱</span>
            <span className="font-semibold text-foreground text-sm">{t('dash.cropStageTimeline')}</span>
            <span className="text-xs text-gray-400 ml-1">— {field.crop} · {t('dash.current')}: {field.stage}</span>
          </div>
          {field.timeline.length > 0 ? (
            <StageTimeline stages={field.timeline} currentStage={field.stage} readOnly currentLabel={t('dash.current')} />
          ) : (
            <div className="text-xs text-gray-400 italic">No stage sequence available for this crop.</div>
          )}
        </div>

        {/* Recommendation History & Agronomist Oversight — real endpoints, never surfaced before */}
        <HistoryOversightPanel fieldId={field.id} onOverridden={() => fetchTwin()} />

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
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center text-sm text-muted">Loading…</div>}>
      <DashboardContent />
    </Suspense>
  );
}
