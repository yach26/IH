"use client";

import { useEffect, useRef } from "react";
import { X, FileText, ShieldCheck } from "lucide-react";
import type { RecommendationOut } from "@/lib/api";

const nutrientNames: Record<string, string> = { N: "N", P2O5: "P₂O₅", K2O: "K₂O" };
const qualityNames: Record<string, string> = {
  soil_report_current: "Current soil report",
  weather_available: "Weather available and checked",
  crop_stage_known: "Crop stage in the supported calendar",
  micronutrients_complete: "Micronutrient measurements recorded",
  has_soil_test: "Confirmed soil test",
  soil_is_fresh: "Soil test within freshness threshold",
  has_crop: "Crop recorded",
  has_rec_type: "Recommendation type recorded",
};

function displayNumber(value: number | null | undefined): string {
  return value == null || !Number.isFinite(value) ? "Not recorded" : String(value);
}

/** Read the persisted proof only; opening this drawer never runs an LLM or optimizer. */
export default function ProofTrace({
  proof, fieldId, selection, onClose,
}: {
  proof: RecommendationOut | null;
  fieldId: string;
  selection: string;
  onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    dialog?.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      dialog?.close();
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, []);

  const required = proof?.why?.required ?? proof?.ledger?.required;
  const measured = proof?.why?.normalized_soil ?? proof?.ledger?.normalized_soil;
  const gap = proof?.why?.gap ?? proof?.ledger?.gap;
  const history = proof?.why?.history ?? proof?.based_on?.application_history ?? proof?.ledger?.application_history;
  const evidence = (proof?.based_on?.evidence ?? []).filter((item) => item.source_file !== "NONE");
  const flags = Array.from(new Set(proof?.flags ?? []));
  const quality = Object.entries(proof?.data_quality ?? {});
  const sources = Array.from(new Set([
    proof?.based_on?.citation,
    proof?.based_on?.conversion_source,
    history?.source,
    proof?.weather_context?.source,
    ...evidence.map((item) => item.citation ?? item.source_file),
  ].filter((value): value is string => Boolean(value))));

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="proof-trace-title"
      aria-describedby="proof-trace-description"
      onCancel={(event) => { event.preventDefault(); onClose(); }}
      onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}
      className="fixed inset-y-0 left-auto right-0 m-0 h-dvh max-h-dvh w-full max-w-2xl overflow-y-auto border-0 bg-surface p-0 text-foreground shadow-2xl backdrop:bg-black/40"
    >
      <div className="min-h-full" onClick={(event) => event.stopPropagation()}>
        <header className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-border bg-surface px-5 py-5 sm:px-7">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">Kisan Saathi · {fieldId}</p>
            <h2 id="proof-trace-title" className="mt-1 text-2xl font-bold">Proof Trace</h2>
            <p id="proof-trace-description" className="mt-1 text-sm text-muted">{selection} · Evidence saved with this recommendation</p>
          </div>
          <button type="button" autoFocus onClick={onClose} aria-label="Close Proof Trace" className="flex min-h-11 min-w-11 items-center justify-center rounded-full border border-border hover:bg-surface-hover">
            <X className="h-5 w-5" />
          </button>
        </header>

        {!proof ? (
          <div className="p-6">
            <p className="font-semibold">No saved proof is available yet.</p>
            <p className="mt-2 text-sm text-muted">Confirm your field and soil details, then generate a new recommendation to create its audit trail.</p>
          </div>
        ) : (
          <div className="space-y-7 px-5 py-6 sm:px-7">
            <section aria-labelledby="proof-gap-title">
              <h3 id="proof-gap-title" className="font-bold">1. Exact soil-gap calculation</h3>
              <p className="mt-2 text-sm text-muted">Gap = max(0, crop requirement − normalized soil measurement − prior application credit). The ledger rounds the gap to 0.1 kg/ha.</p>
              <p className="mt-1 text-xs text-muted">All values below use kg/ha of N, P₂O₅ and K₂O. The soil report’s P and K values are normalized to the same nutrient basis first.</p>
              {required && measured && gap ? (
                <div className="mt-4 overflow-x-auto rounded-lg border border-border">
                  <table className="w-full text-left text-sm">
                    <caption className="sr-only">Saved nutrient ledger: requirement minus normalized soil minus credited nutrients equals actionable gap</caption>
                    <thead className="bg-surface-hover text-xs text-muted"><tr><th className="p-3">Nutrient</th><th className="p-3">Required</th><th className="p-3">Soil</th><th className="p-3">Credit</th><th className="p-3">Gap</th></tr></thead>
                    <tbody>{["N", "P2O5", "K2O"].map((nutrient) => (
                      <tr key={nutrient} className="border-t border-border">
                        <th className="p-3">{nutrientNames[nutrient]}</th>
                        <td className="p-3 tabular-nums">{displayNumber(required[nutrient])}</td>
                        <td className="p-3 tabular-nums">{displayNumber(measured[nutrient])}</td>
                        <td className="p-3 tabular-nums">{displayNumber(history?.credits_kg_ha?.[nutrient])}</td>
                        <td className="p-3 font-bold tabular-nums text-primary">{displayNumber(gap[nutrient])}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              ) : <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">A complete nutrient calculation is not available for this recommendation. {proof.reason}</p>}
              {proof.why?.soil && <p className="mt-3 text-sm">Reported measurements: {proof.why.soil}</p>}
              {proof.based_on?.conversion_source && <p className="mt-2 break-words text-xs text-muted">Conversion source: {proof.based_on.conversion_source}</p>}
              <div className="mt-4 rounded-lg bg-surface-hover p-4 text-sm">
                <p className="font-semibold">Prior fertilizer applications</p>
                <p className="mt-1 text-muted">{history ? history.status.replaceAll("_", " ") : "History credit was not recorded in this proof."}</p>
                {history?.reason && <p className="mt-1 text-amber-800">{history.reason}</p>}
                {history?.applications?.map((application) => <p key={application.application_id} className="mt-2">{application.application_date} · {application.product} · {application.status.replaceAll("_", " ")}</p>)}
                {history?.assumptions?.map((assumption) => <p key={assumption} className="mt-2 text-xs text-muted">{assumption}</p>)}
                <p className="mt-2 text-xs text-muted">Only recorded applications can be credited. Missing records do not establish that no fertilizer was applied.</p>
              </div>
              <p className="mt-3 text-xs text-muted">Quantities are copied from the saved Nutrient Ledger and Optimizer output. This drawer does not calculate or change a fertilizer plan.</p>
            </section>

            <section aria-labelledby="proof-rdf-title">
              <h3 id="proof-rdf-title" className="flex items-center gap-2 font-bold"><FileText className="h-4 w-4 text-primary" />2. RDF citation and retrieved evidence</h3>
              <p className="mt-2 break-words text-sm">{proof.based_on?.citation || "No RDF citation was recorded."}</p>
              {evidence.length ? evidence.map((item, index) => (
                <article key={`${item.source_file}-${index}`} className="mt-3 rounded-lg border border-border p-4">
                  <p className="break-words text-sm font-semibold">{item.citation || item.source_file || "Source label unavailable"}</p>
                  <blockquote className="mt-2 whitespace-pre-wrap border-l-2 border-primary/30 pl-3 text-sm leading-relaxed text-muted">{item.excerpt || item.content || "No paragraph excerpt was saved for this source."}</blockquote>
                </article>
              )) : <p className="mt-3 text-sm text-muted">No relevant RAG paragraph was saved. The RDF citation above is distinct from retrieved supporting evidence.</p>}
            </section>

            <section aria-labelledby="proof-weather-title">
              <h3 id="proof-weather-title" className="font-bold">3. Weather window reasoning</h3>
              <p className="mt-2 text-sm font-semibold">{proof.when || "No application window issued."}</p>
              <p className="mt-2 text-sm text-muted">{proof.why?.weather || "Weather reasoning was not recorded."}</p>
              {proof.weather_context?.rainfall_mm_next_7d != null && <p className="mt-2 text-sm">Forecast rain over 7 days: {proof.weather_context.rainfall_mm_next_7d} mm</p>}
              <p className="mt-2 text-xs text-muted">Source: {proof.weather_context?.source || "Not recorded"} · Status: {proof.weather_context?.status?.replaceAll("_", " ") || "Not recorded"}</p>
              {proof.weather_context?.flags?.map((flag) => <p key={flag} className="mt-2 break-words text-xs text-amber-800">{flag}</p>)}
            </section>

            <section aria-labelledby="proof-confidence-title">
              <h3 id="proof-confidence-title" className="flex items-center gap-2 font-bold"><ShieldCheck className="h-4 w-4 text-primary" />4. Confidence breakdown</h3>
              <p className="mt-2 text-sm">Recorded confidence: <strong>{proof.confidence}</strong></p>
              <p className="mt-1 text-xs text-muted">This is a rule-based evidence and data-quality rating, not a probability of yield or a guarantee.</p>
              {quality.length > 0 && <dl className="mt-3 divide-y divide-border rounded-lg border border-border px-3">{quality.map(([key, passed]) => (
                <div key={key} className="flex items-start justify-between gap-3 py-3 text-sm"><dt>{qualityNames[key] || key.replaceAll("_", " ")}</dt><dd className={`shrink-0 font-semibold ${passed ? "text-primary" : "text-amber-800"}`}>{passed ? "Recorded / passed" : "Missing / needs review"}</dd></div>
              ))}</dl>}
              {flags.length ? <ul className="mt-3 space-y-2 text-sm text-amber-900">{flags.map((flag) => <li key={flag} className="break-words rounded-lg bg-amber-50 p-3">{flag}</li>)}</ul> : <p className="mt-3 text-sm text-muted">No confidence flags were saved.</p>}
              {proof.validation?.warnings?.map((warning) => <p key={warning} className="mt-2 text-sm text-amber-900">{warning}</p>)}
              {proof.validation?.blocking_issues?.map((issue) => <p key={issue} className="mt-2 text-sm text-red-800">{issue}</p>)}
              {proof.required_actions?.length > 0 && <div className="mt-4"><h4 className="text-sm font-semibold">What we need next</h4><ul className="mt-2 list-disc space-y-2 pl-5 text-sm">{proof.required_actions.map((action) => <li key={action}>{action}</li>)}</ul></div>}
            </section>

            <section aria-labelledby="proof-sources-title">
              <h3 id="proof-sources-title" className="font-bold">5. Source documents and field records</h3>
              {sources.length ? <ul className="mt-3 list-disc space-y-2 break-words pl-5 text-sm text-muted">{sources.map((source) => <li key={source}>{source}</li>)}</ul> : <p className="mt-2 text-sm text-muted">No source documents were recorded.</p>}
              {proof.based_on?.farm_data?.length ? <ul className="mt-4 space-y-1 text-xs text-muted">{proof.based_on.farm_data.map((record) => <li key={record}>{record}</li>)}</ul> : null}
            </section>
          </div>
        )}
      </div>
    </dialog>
  );
}
