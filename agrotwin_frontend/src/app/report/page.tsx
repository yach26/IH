"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle, CheckCircle2, ChevronRight, Download,
  FlaskConical, Leaf, LoaderCircle, MapPin, Printer,
  ShieldCheck, TrendingDown, TrendingUp, Minus,
} from "lucide-react";
import { getTwin, getLatestRecommendation, ApiError, type TwinResponse } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined, decimals = 1): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toFixed(decimals);
}

function fmtCost(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

function soilStatus(score: number | null): "Deficient" | "Optimal" | "Excess" {
  if (score == null) return "Optimal";
  if (score < 50) return "Deficient";
  if (score > 120) return "Excess";
  return "Optimal";
}

function soilStatusColor(s: "Deficient" | "Optimal" | "Excess"): string {
  if (s === "Deficient") return "text-red-600 bg-red-50 border-red-200";
  if (s === "Excess") return "text-amber-700 bg-amber-50 border-amber-200";
  return "text-green-700 bg-green-50 border-green-200";
}

function confidenceColor(c: string): string {
  if (c === "HIGH") return "text-green-700 bg-green-50 border-green-200";
  if (c === "MEDIUM") return "text-amber-700 bg-amber-50 border-amber-200";
  if (c === "LOW") return "text-orange-700 bg-orange-50 border-orange-200";
  if (c === "ABSTAIN") return "text-red-700 bg-red-50 border-red-200";
  return "text-gray-600 bg-gray-50 border-gray-200";
}

function productDisplayName(key: string): string {
  return key.replace(/_kg_ha$/i, "").replace(/_/g, " ");
}

function gapColor(gap: number): string {
  if (gap > 20) return "text-red-600";
  if (gap < -20) return "text-amber-600";
  return "text-green-600";
}

// ─── Section Components ────────────────────────────────────────────────────────

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-4 pb-2 border-b border-border">
      <span className="text-primary">{icon}</span>
      <h2 className="text-base font-bold text-foreground uppercase tracking-wide">{title}</h2>
    </div>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-surface border border-border rounded-xl p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

// ─── ABSTAIN State ─────────────────────────────────────────────────────────────

function AbstainReport({
  fieldId, reason, requiredActions, flags,
}: { fieldId: string; reason: string | null; requiredActions: string[]; flags: string[] }) {
  return (
    <div className="max-w-3xl mx-auto px-4 md:px-6 py-8 space-y-6">
      <Card className="border-red-200 bg-red-50/30">
        <div className="flex gap-3 items-start">
          <AlertTriangle className="w-6 h-6 text-red-600 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h2 className="font-bold text-red-800 text-base mb-1">A reliable fertilizer plan cannot currently be produced</h2>
            <p className="text-sm text-red-700 leading-relaxed">{reason || "The recommendation pipeline abstained. See required actions below."}</p>
          </div>
        </div>
      </Card>
      {requiredActions.length > 0 && (
        <Card>
          <h3 className="font-semibold text-sm mb-3">Required before a plan can be issued</h3>
          <ol className="space-y-2">
            {requiredActions.map((action, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground">
                <span className="font-bold text-primary shrink-0">{i + 1}.</span>
                <span>{action}</span>
              </li>
            ))}
          </ol>
        </Card>
      )}
      {flags.length > 0 && (
        <Card>
          <h3 className="font-semibold text-xs uppercase tracking-wide text-muted mb-3">Flags</h3>
          <ul className="space-y-1 text-xs text-muted">
            {flags.map((f, i) => <li key={i} className="font-mono">{f}</li>)}
          </ul>
        </Card>
      )}
      <div className="flex gap-3 flex-wrap">
        <Link href={`/upload?field=${encodeURIComponent(fieldId)}`} className="inline-flex items-center gap-2 min-h-11 bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-5 py-2 rounded-lg">
          Upload New Soil Report
        </Link>
        <Link href={`/dashboard?field=${encodeURIComponent(fieldId)}`} className="inline-flex items-center gap-2 min-h-11 border border-border bg-surface text-foreground text-sm font-semibold px-5 py-2 rounded-lg hover:bg-background">
          View Dashboard
        </Link>
      </div>
    </div>
  );
}

// ─── Main Report Content ───────────────────────────────────────────────────────

function ReportContent({ fieldId }: { fieldId: string }) {
  const { t } = useLanguage();
  const [twin, setTwin] = React.useState<TwinResponse | null>(null);
  const [plan, setPlan] = React.useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([getTwin(fieldId), getLatestRecommendation(fieldId).catch(() => null)])
      .then(([t, p]) => {
        if (cancelled) return;
        setTwin(t);
        setPlan(p as Record<string, unknown> | null);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Could not load report data.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [fieldId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 gap-3">
        <LoaderCircle className="w-8 h-8 animate-spin text-primary" aria-hidden="true" />
        <p className="text-sm text-muted">Loading field report…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700 text-sm">{error}</div>
        <Link href={`/dashboard?field=${encodeURIComponent(fieldId)}`} className="mt-4 inline-flex items-center gap-2 text-sm text-primary underline">← View Dashboard</Link>
      </div>
    );
  }
  if (!twin) return null;

  const cp = twin.currentPlan;
  const status = cp.status;
  const isAbstain = status === "ABSTAIN";

  if (isAbstain) {
    return (
      <AbstainReport
        fieldId={fieldId}
        reason={cp.reason ?? null}
        requiredActions={cp.requiredActions ?? []}
        flags={cp.flags ?? []}
      />
    );
  }

  // ── Data extraction ──────────────────────────────────────────────────────
  const howMuch = cp.fertilizerBreakdown || {};
  const area = twin.area_ha || 0;
  const soilGap = cp.soilGap || {};
  const nutrients = twin.nutrients;
  const soilDetail = twin.soilDetail;

  // Nutrient gap table: required vs available vs gap
  type NutrientRow = { label: string; required: number | null; available: number | null; gap: number | null; unit: string };
  const nutrientRows: NutrientRow[] = [
    {
      label: "Nitrogen (N)",
      required: nutrients.n.target,
      available: nutrients.n.current,
      gap: (nutrients.n.target != null && nutrients.n.current != null)
        ? Number((nutrients.n.target - nutrients.n.current).toFixed(1)) : null,
      unit: "kg N/ha",
    },
    {
      label: "Phosphorus (P₂O₅)",
      required: nutrients.p.target,
      available: nutrients.p.current,
      gap: (nutrients.p.target != null && nutrients.p.current != null)
        ? Number((nutrients.p.target - nutrients.p.current).toFixed(1)) : null,
      unit: "kg P₂O₅/ha",
    },
    {
      label: "Potassium (K₂O)",
      required: nutrients.k.target,
      available: nutrients.k.current,
      gap: (nutrients.k.target != null && nutrients.k.current != null)
        ? Number((nutrients.k.target - nutrients.k.current).toFixed(1)) : null,
      unit: "kg K₂O/ha",
    },
  ];

  const costPerHa = cp.estimatedCost;
  const totalCost = (costPerHa != null && area > 0) ? costPerHa * area : null;

  // Evidence
  const evidence: { source_file?: string; citation?: string; excerpt?: string }[] =
    ((plan as Record<string, unknown> | null)?.based_on as { evidence?: unknown[] } | null | undefined)?.evidence as typeof evidence || [];

  // Next steps from when + required_actions
  const when = cp.applicationWindow && cp.applicationWindow !== "N/A" ? cp.applicationWindow : null;
  const nextSteps: string[] = [];
  if (Object.keys(howMuch).length > 0) {
    nextSteps.push(`Purchase: ${Object.entries(howMuch).map(([k, v]) => `${productDisplayName(k)} — ${fmt(v as number)} kg/ha`).join(", ")}.`);
  }
  if (when) nextSteps.push(`Apply between: ${when}.`);
  if (cp.requiredActions?.length) cp.requiredActions.forEach(a => nextSteps.push(a));
  nextSteps.push("Re-run the recommendation after heavy rain (>50 mm) or a new soil test.");

  // Soil status table
  const soilStatusRows = [
    { label: "Nitrogen (N)", score: soilDetail.n_score, unit: "kg/ha", value: nutrients.n.current },
    { label: "Phosphorus (P₂O₅)", score: soilDetail.p_score, unit: "kg P₂O₅/ha", value: nutrients.p.current },
    { label: "Potassium (K₂O)", score: soilDetail.k_score, unit: "kg K₂O/ha", value: nutrients.k.current },
    { label: "Soil pH", score: null, unit: "", value: soilDetail.ph },
    { label: "Organic Carbon (OC)", score: null, unit: "%", value: soilDetail.oc_percent },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 md:px-6 py-8 space-y-8 print:space-y-6">

      {/* ── Field Summary ── */}
      <Card>
        <SectionHeader icon={<MapPin className="w-4 h-4" />} title="Field Summary" />
        <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3 text-sm">
          {[
            ["Field ID", twin.fieldId],
            ["Crop", twin.crop],
            ["Growth Stage", twin.growthStage || "—"],
            ["Area", area > 0 ? `${area} ha` : "—"],
            ["Location", twin.location || "Not provided"],
            ["Soil Health Score", twin.soilHealthScore != null ? `${twin.soilHealthScore}/100` : "—"],
          ].map(([label, value]) => (
            <div key={label as string}>
              <dt className="text-xs text-muted uppercase tracking-wide">{label}</dt>
              <dd className="font-semibold text-foreground mt-0.5">{value as string}</dd>
            </div>
          ))}
        </dl>
      </Card>

      {/* ── Soil Status ── */}
      <Card>
        <SectionHeader icon={<FlaskConical className="w-4 h-4" />} title="Soil Status" />
        {!twin.hasSoilTest ? (
          <p className="text-sm text-muted">No soil test recorded for this field.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 pr-4 font-semibold text-xs uppercase tracking-wide text-muted">Nutrient</th>
                  <th className="text-right py-2 pr-4 font-semibold text-xs uppercase tracking-wide text-muted">Value</th>
                  <th className="text-right py-2 font-semibold text-xs uppercase tracking-wide text-muted">Status</th>
                </tr>
              </thead>
              <tbody>
                {soilStatusRows.map(({ label, score, value, unit }) => {
                  const s = soilStatus(score);
                  return (
                    <tr key={label} className="border-b border-border/50">
                      <td className="py-2.5 pr-4 text-foreground">{label}</td>
                      <td className="py-2.5 pr-4 text-right font-mono text-foreground">
                        {value != null ? `${fmt(value as number, 2)}${unit ? ` ${unit}` : ""}` : "—"}
                      </td>
                      <td className="py-2.5 text-right">
                        {score != null ? (
                          <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full border ${soilStatusColor(s)}`}>{s}</span>
                        ) : (
                          <span className="text-muted text-xs">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ── Nutrient Gap ── */}
      <Card>
        <SectionHeader icon={<TrendingDown className="w-4 h-4" />} title="Nutrient Gap" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-border">
                {["Nutrient", "Required", "Available", "Gap", "Unit"].map(h => (
                  <th key={h} className={`py-2 font-semibold text-xs uppercase tracking-wide text-muted ${h === "Nutrient" ? "text-left pr-4" : "text-right"}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {nutrientRows.map((row) => (
                <tr key={row.label} className="border-b border-border/50">
                  <td className="py-2.5 pr-4 text-foreground">{row.label}</td>
                  <td className="py-2.5 text-right font-mono">{fmt(row.required)}</td>
                  <td className="py-2.5 text-right font-mono">{fmt(row.available)}</td>
                  <td className={`py-2.5 text-right font-mono font-semibold ${gapColor(row.gap ?? 0)}`}>
                    {row.gap != null ? (row.gap > 0 ? `+${fmt(row.gap)}` : fmt(row.gap)) : "—"}
                  </td>
                  <td className="py-2.5 text-right text-xs text-muted">{row.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-muted mt-3">Positive gap = deficit (apply fertilizer). Negative gap = excess (monitor only).</p>
          <p className="text-xs text-muted mt-1">Conversions: FAO Appendix Table 16 (P × 2.2919 = P₂O₅; K × 1.2046 = K₂O).</p>
        </div>
      </Card>

      {/* ── Fertilizer Plan (Hero) ── */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Leaf className="w-5 h-5 text-primary" aria-hidden="true" />
          <h2 className="text-lg font-bold text-foreground uppercase tracking-wide">Fertilizer Plan</h2>
          {cp.status && (
            <span className="text-xs px-2 py-0.5 rounded-full border font-semibold bg-green-50 text-green-700 border-green-200">
              {cp.status.replace(/_/g, " ")}
            </span>
          )}
        </div>
        {Object.keys(howMuch).length === 0 ? (
          <Card className="border-amber-200">
            <p className="text-sm text-amber-900">{cp.nextAction || "No fertilizer products specified in the current plan."}</p>
          </Card>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(howMuch).map(([key, kgPerHa]) => {
              const name = productDisplayName(key);
              const totalKg = area > 0 ? (kgPerHa as number) * area : null;
              return (
                <div key={key} className="bg-gradient-to-br from-primary/5 to-primary/10 border-2 border-primary/20 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
                  <div className="text-xs font-bold uppercase tracking-widest text-primary mb-3">{name}</div>
                  <div className="text-4xl font-black text-foreground leading-none">
                    {fmt(kgPerHa as number, 1)}
                    <span className="text-base font-semibold text-muted ml-1">kg/ha</span>
                  </div>
                  {totalKg != null && (
                    <div className="mt-3 pt-3 border-t border-primary/10">
                      <span className="text-xs text-muted">Total for {area} ha field: </span>
                      <span className="font-bold text-foreground">{fmt(totalKg, 1)} kg</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Application Window ── */}
      {when && (
        <Card>
          <SectionHeader icon={<CheckCircle2 className="w-4 h-4" />} title="Application Window" />
          <p className="text-sm font-semibold text-foreground mb-2">{when}</p>
          {twin.weather.condition && (
            <p className="text-xs text-muted">{twin.weather.condition}</p>
          )}
          {twin.weather.heavy_rain_alert && (
            <div className="mt-2 flex items-center gap-2 text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden="true" />
              Heavy rain alert active — defer application until dry conditions.
            </div>
          )}
        </Card>
      )}

      {/* ── Cost ── */}
      <Card>
        <SectionHeader icon={<TrendingUp className="w-4 h-4" />} title="Estimated Cost" />
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-xs text-muted uppercase tracking-wide mb-1">Per hectare</p>
            <p className="text-2xl font-black text-foreground">{fmtCost(costPerHa)}</p>
          </div>
          {area > 0 && (
            <div>
              <p className="text-xs text-muted uppercase tracking-wide mb-1">Total ({area} ha)</p>
              <p className="text-2xl font-black text-foreground">{fmtCost(totalCost)}</p>
            </div>
          )}
        </div>
        {cp.costCitation && <p className="text-xs text-muted mt-3">{cp.costCitation}</p>}
        <p className="text-xs text-muted mt-2 italic">Note: MOP price (₹36/kg) is an engineering assumption, not a verified current market rate. Costs exclude transport, labour and application expenses.</p>
        <p className="text-xs text-muted mt-1 italic">Savings vs typical practice cannot be shown — the survey denominator (per field / per ha / per season) is unconfirmed.</p>
      </Card>

      {/* ── Next Steps ── */}
      <Card>
        <SectionHeader icon={<ChevronRight className="w-4 h-4" />} title="Next Steps" />
        <ol className="space-y-3">
          {nextSteps.map((step, i) => (
            <li key={i} className="flex gap-3 text-sm">
              <span className="shrink-0 w-6 h-6 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">{i + 1}</span>
              <span className="text-foreground leading-relaxed">{step}</span>
            </li>
          ))}
        </ol>
      </Card>

      {/* ── Why this plan ── */}
      <Card>
        <SectionHeader icon={<ShieldCheck className="w-4 h-4" />} title="Why This Plan" />
        <div className="space-y-3 text-sm">
          {cp.citation && <p className="text-foreground leading-relaxed">{cp.citation}</p>}
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted uppercase tracking-wide mb-1">Confidence</p>
              <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full border ${confidenceColor(cp.confidence)}`}>
                {cp.confidence}
              </span>
            </div>
            {cp.flags?.length > 0 && (
              <div>
                <p className="text-xs text-muted uppercase tracking-wide mb-1">Flags</p>
                <ul className="space-y-0.5">
                  {cp.flags.slice(0, 5).map((f, i) => (
                    <li key={i} className="text-xs font-mono text-muted">{f}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* ── Evidence / Citations ── */}
      {evidence.length > 0 && (
        <Card>
          <SectionHeader icon={<FlaskConical className="w-4 h-4" />} title="Evidence & Citations" />
          <div className="space-y-4">
            {evidence.slice(0, 4).map((item, i) => (
              <div key={i} className="border-l-2 border-primary/30 pl-4">
                <p className="text-xs font-semibold text-primary mb-1">{item.source_file || "Source"}</p>
                {item.citation && <p className="text-xs text-muted mb-1 italic">{item.citation}</p>}
                {item.excerpt && <p className="text-xs text-foreground leading-relaxed">{item.excerpt}</p>}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ── What Happens Next ── */}
      <Card className="bg-primary/3 border-primary/20">
        <SectionHeader icon={<Leaf className="w-4 h-4" />} title="What Happens Next" />
        <ul className="space-y-2 text-sm text-foreground">
          <li className="flex gap-2"><Minus className="w-4 h-4 text-primary shrink-0 mt-0.5" />Kisan Saathi continuously monitors weather. Heavy rain (&gt;50 mm/7d) will automatically trigger a revised application window.</li>
          <li className="flex gap-2"><Minus className="w-4 h-4 text-primary shrink-0 mt-0.5" />After applying fertilizer, record the application on the dashboard — it updates the nutrient ledger for the next recommendation.</li>
          <li className="flex gap-2"><Minus className="w-4 h-4 text-primary shrink-0 mt-0.5" />A new soil test is recommended at the next crop stage. Upload the report when available to generate a fresh plan.</li>
        </ul>
      </Card>

      {/* ── Actions ── */}
      <div className="flex gap-3 flex-wrap print:hidden">
        <button onClick={() => window.print()} className="inline-flex items-center gap-2 min-h-11 bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-5 py-2 rounded-lg">
          <Printer className="w-4 h-4" aria-hidden="true" /> Print / Save PDF
        </button>
        <Link href={`/dashboard?field=${encodeURIComponent(fieldId)}`} className="inline-flex items-center gap-2 min-h-11 border border-border bg-surface text-foreground text-sm font-semibold px-5 py-2 rounded-lg hover:bg-background">
          ← Dashboard
        </Link>
        <Link href={`/simulator?field=${encodeURIComponent(fieldId)}`} className="inline-flex items-center gap-2 min-h-11 border border-border bg-surface text-foreground text-sm font-semibold px-5 py-2 rounded-lg hover:bg-background">
          What-If Simulator
        </Link>
      </div>
    </div>
  );
}

// ─── Page Shell ───────────────────────────────────────────────────────────────

function ReportShell() {
  const searchParams = useSearchParams();
  const fieldId = searchParams.get("field") || "";

  return (
    <div className="min-h-screen bg-background font-sans">
      {/* Print-optimised header */}
      <header className="sticky top-0 z-30 bg-surface border-b border-border px-4 md:px-6 py-4 print:static print:border-0">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-primary mb-1">Kisan Saathi · Field Report</p>
            <h1 className="font-serif text-xl font-bold text-foreground">
              Fertilizer Analysis Report{fieldId ? ` — ${fieldId}` : ""}
            </h1>
          </div>
          <div className="print:hidden flex gap-2 items-center">
            <Link href={`/upload?field=${encodeURIComponent(fieldId)}`} className="text-xs text-primary underline">Upload New Soil Report</Link>
          </div>
        </div>
      </header>

      {!fieldId ? (
        <div className="max-w-3xl mx-auto px-4 py-16 text-center">
          <p className="text-muted text-sm">No field selected. Go to the dashboard and select a field first.</p>
          <Link href="/dashboard" className="mt-4 inline-flex items-center text-sm text-primary underline">← Go to Dashboard</Link>
        </div>
      ) : (
        <ReportContent fieldId={fieldId} />
      )}

      {/* Print footer */}
      <footer className="hidden print:block text-xs text-muted mt-8 border-t border-border pt-4 px-6">
        <p>Kisan Saathi · Sustainable Fertilizer Usage Optimizer · Generated {new Date().toLocaleDateString("en-IN")}</p>
        <p>Nutrient conversions: FAO Appendix Table 16. Prices: IFFCO reference list (Jan 2025). MOP price is an engineering assumption.</p>
      </footer>
    </div>
  );
}

export default function ReportPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoaderCircle className="w-8 h-8 animate-spin text-primary" aria-hidden="true" />
      </div>
    }>
      <ReportShell />
    </Suspense>
  );
}
