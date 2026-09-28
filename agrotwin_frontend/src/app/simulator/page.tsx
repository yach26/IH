"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { whatIf, recommend, type WhatIfResponse, type WhatIfPlanSide } from "@/lib/api";
import { useFieldParam } from "@/lib/useFieldParam";
import FieldOnboarding from "@/components/ui/FieldOnboarding";

const nutrients = ["N", "P2O5", "K2O"];
const number = (value: number) => value.toLocaleString("en-IN", { maximumFractionDigits: 2 });
const money = (value: number | null) => value === null ? "Not priced" : `INR ${number(value)}/ha`;
const panel = "rounded-2xl border border-slate-200 bg-white p-5 md:p-6";

function NutrientChart({ baseline, scenario }: { baseline: WhatIfPlanSide; scenario: WhatIfPlanSide }) {
  return <section className={panel} aria-labelledby="nutrient-chart-title">
    <h2 id="nutrient-chart-title" className="text-xl font-bold">Does the mix cover the remaining nutrient need?</h2>
    <p className="mt-2 text-sm text-slate-600">Remaining need is the crop requirement after soil nutrients and supported application credits. All amounts are kg/ha, on the same N / P2O5 / K2O basis.</p>
    <div className="mt-5 grid gap-6 md:grid-cols-3">{nutrients.map(n => {
      const rows = [
        { label: "Remaining need", amount: baseline.gap[n], color: "bg-slate-500" },
        { label: "Baseline supplies", amount: baseline.nutrientsSupplied[n], color: "bg-emerald-700" },
        { label: "Scenario supplies", amount: scenario.nutrientsSupplied[n], color: "bg-blue-600" },
      ];
      const max = Math.max(1, ...rows.map(r => r.amount));
      return <figure key={n} className="min-w-0 space-y-3"><figcaption className="font-bold">{n}</figcaption>
        {rows.map(row => <div key={row.label}><div className="flex justify-between gap-2 text-xs"><span>{row.label}</span><strong>{number(row.amount)}</strong></div><div className="mt-1 h-3 rounded bg-slate-100" aria-hidden="true"><div className={`h-3 rounded ${row.color}`} style={{width: `${row.amount / max * 100}%`}} /></div></div>)}
        <p className="text-sm">Scenario excess: <strong>{number(scenario.excess[n])}</strong><br/>Scenario shortfall: <strong>{number(scenario.shortfall[n])}</strong></p>
      </figure>;
    })}</div>
    <p className="mt-4 text-xs text-slate-500">Each nutrient uses its own scale. Values are calculated nutrient supply, not a prediction of plant uptake or yield.</p>
  </section>;
}

function Report({ result }: { result: WhatIfResponse }) {
  const baseline = result.original!;
  const scenario = result.simulated!;
  const issues = [...scenario.validation.blocking_issues, ...scenario.validation.warnings];
  const products = [...new Set([...Object.keys(baseline.quantities), ...Object.keys(scenario.quantities)])];
  const costChange = result.deltaCost;
  return <div className="space-y-5" aria-label="Scenario comparison report">
    <section className={panel}>
      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Calculated comparison / {result.crop || "Selected crop"}</p>
      <h2 className="mt-2 text-2xl font-bold">What changes in this scenario?</h2>
      <p className="mt-2 text-slate-600">{costChange === null ? "A complete price is unavailable for this mix." : costChange === 0 ? "The product cost is unchanged from the baseline." : `This mix costs ${money(Math.abs(costChange))} ${costChange < 0 ? "less" : "more"} than the baseline.`} A lower cost alone does not make the mix agronomically suitable. Check the nutrient shortfalls and constraints below.</p>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-emerald-50 p-4"><h3 className="text-sm">Baseline product cost</h3><p className="mt-2 text-xl font-bold">{money(baseline.cost)}</p></div>
        <div className="rounded-xl bg-blue-50 p-4"><h3 className="text-sm">Scenario product cost</h3><p className="mt-2 text-xl font-bold">{money(scenario.cost)}</p></div>
        <div className="rounded-xl bg-slate-100 p-4"><h3 className="text-sm">Cost difference</h3><p className="mt-2 text-xl font-bold">{costChange === null ? "Unavailable" : `${costChange > 0 ? "+" : costChange < 0 ? "-" : ""}${money(Math.abs(costChange))}`}</p></div>
      </div>
    </section>
    <NutrientChart baseline={baseline} scenario={scenario}/>
    <section className={panel}>
      <h2 className="text-xl font-bold">Product-by-product comparison</h2>
      <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Fertilizer quantities in kg/ha</caption>
        <thead><tr className="border-b"><th className="py-3 pr-3">Product</th><th className="p-3">Baseline</th><th className="p-3">Scenario</th><th className="p-3">Change</th></tr></thead>
        <tbody>{products.map(p => { const a = baseline.quantities[p] || 0, b = scenario.quantities[p] || 0; return <tr key={p} className="border-b"><th className="py-3 pr-3">{p.replace("_kg_ha", "")}</th><td className="p-3">{number(a)}</td><td className="p-3">{number(b)}</td><td className="p-3">{b > a ? "+" : ""}{number(b-a)}</td></tr>; })}</tbody>
      </table></div><p className="mt-2 text-xs text-slate-600">All quantities in kg/ha. A zero mix means no fertilizer in this hypothetical comparison, not a recommendation to stop fertilizing.</p>
    </section>
    <section className={panel}>
      <h2 className="text-xl font-bold">Constraints and rainfall precautions</h2>
      <p className="mt-2 font-semibold">{scenario.validation.is_valid ? "No blocking constraint detected by the configured checks." : "This scenario fails a constraint check. Do not treat it as an application recommendation."}</p>
      <p className="mt-2 text-sm">Baseline timing: {baseline.applicationWindow || "No validated window recorded."}</p>
      <p className="mt-2 text-sm">Scenario seven-day rain: {scenario.rainfallMm == null ? "Unavailable" : `${number(scenario.rainfallMm)} mm`}. {scenario.applicationWindow}</p>
      <ul className="mt-4 list-disc space-y-2 pl-5 text-sm">{[...new Set([...issues, ...scenario.sustainabilityNotes])].map(text => <li key={text}>{text}</li>)}</ul>
    </section>
    <details className={panel}><summary className="cursor-pointer font-semibold">Sources, confidence and limits of this report</summary>
      <div className="mt-4 space-y-3 text-sm break-words">
        <p>Saved recommendation confidence: {baseline.confidence}. Scenario confidence is not assessed: scaling quantities does not transfer the baseline confidence to this new mix.</p>
        <p>{baseline.costCitation}</p><p>Formula: sum of product quantity (kg/ha) multiplied by its price (INR/kg). Both sides use the same price table; labour and transport are excluded.</p>
        <p><strong>Yield effect is not calculated.</strong> {result.yieldReason}</p>
        <p>Seasonal savings versus farmer practice cannot be calculated because the 47-farmer survey does not establish the quantity basis or season.</p>
        <ul className="list-disc pl-5">{result.notes.map(note => <li key={note}>{note}</li>)}</ul>
      </div>
    </details>
  </div>;
}

function FieldSimulator({ fieldId }: { fieldId: string }) {
  const [delta, setDelta] = useState("0");
  const [rain, setRain] = useState("");
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [generationIssue, setGenerationIssue] = useState("");
  useEffect(() => {
    let cancelled = false;
    whatIf(fieldId, { fertilizer_delta_pct: 0 }).then(data => { if (!cancelled) setResult(data); })
      .catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : "Could not check the baseline."); })
      .finally(() => { if (!cancelled) setBusy(false); });
    return () => { cancelled = true; };
  }, [fieldId]);
  async function compare(reset = false, generate = false) {
    setBusy(true); setError(""); setGenerationIssue(""); setResult(null);
    try {
      if (generate) {
        const proof = await recommend(fieldId);
        if (proof.status === "ABSTAIN") setGenerationIssue(proof.reason || "More field information is required.");
      }
      setResult(await whatIf(fieldId, { fertilizer_delta_pct: reset ? 0 : Number(delta), ...(!reset && rain.trim() ? {rainfall_mm: Number(rain)} : {}) }));
    } catch (err) { setError(err instanceof Error ? err.message : "Comparison failed. Please retry."); }
    finally { setBusy(false); }
  }
  const ready = result?.status === "SIMULATION" && result.original && result.simulated;
  return <main className="mx-auto max-w-5xl space-y-6 p-4 md:p-8">
    <header><p className="text-sm font-semibold text-emerald-800">Field {fieldId}</p><h1 className="mt-2 text-3xl font-bold">Fertilizer scenario report</h1><p className="mt-3 text-slate-600">See how changing your saved fertilizer mix affects nutrient supply and product cost. This comparison does not record an application.</p><Link className="mt-3 inline-block underline" href={`/dashboard?field=${encodeURIComponent(fieldId)}`}>View field data and Proof Trace</Link></header>
    <ol aria-label="How the comparison works" className="grid gap-3 text-sm sm:grid-cols-3">{["1. Confirm soil and crop", "2. Generate a baseline plan", "3. Compare nutrients and cost"].map(step => <li key={step} className="rounded-lg border bg-white p-3">{step}</li>)}</ol>
    <form className={panel} onSubmit={e => { e.preventDefault(); void compare(); }}>
      <fieldset disabled={busy} className="flex flex-wrap items-end gap-4 disabled:opacity-60">
        <label className="grid gap-2 text-sm font-medium">Change all fertilizer quantities (%)<input className="rounded border p-3" type="number" min="-100" max="500" step="any" required value={delta} onChange={e => { setDelta(e.target.value); setResult(null); }} /></label>
        <label className="grid gap-2 text-sm font-medium">Hypothetical seven-day rain (mm)<input className="rounded border p-3" placeholder="Use saved weather context" type="number" min="0" step="any" value={rain} onChange={e => { setRain(e.target.value); setResult(null); }} /></label>
        <button className="rounded bg-emerald-800 px-5 py-3 text-white">Compare scenario</button>
        <button type="button" className="rounded border px-4 py-3" onClick={() => { setDelta("0"); setRain(""); void compare(true); }}>Reset to baseline</button>
      </fieldset><p className="mt-3 text-xs text-slate-600">For example, -20% compares 80% of each baseline product. Rainfall changes the precaution checks, not the nutrient quantities or a yield forecast.</p>
    </form>
    {busy && <p role="status">Preparing the comparison...</p>}
    {error && <p role="alert" className="rounded border border-red-200 p-4 text-red-800">{error}</p>}
    {!busy && result && !ready && <section className={`${panel} border-amber-300`}>
      <h2 className="text-xl font-bold">A current baseline is needed</h2><p className="mt-3">{generationIssue || result.reason}</p>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">{result.requiredActions.map(action => <li key={action}>{action}</li>)}</ul>
      <button className="mt-5 rounded bg-emerald-800 px-5 py-3 text-white" onClick={() => void compare(false, true)}>Generate baseline and compare</button>
      <p className="mt-2 text-xs text-slate-600">This saves a new recommendation from your current field data, then reruns the comparison. It does not record fertilizer application.</p>
    </section>}
    {!busy && ready && result && <Report result={result}/>}
    {!busy && !error && !result && <p role="status">Inputs changed. Select Compare scenario to update the report.</p>}
  </main>;
}
function Simulator() {
  const { fieldId, fields, fieldsError, fieldsLoaded, setFieldId } = useFieldParam();
  if (!fieldsLoaded) return <p className="p-6" role="status">Loading your fields...</p>;
  if (!fieldId) return <FieldOnboarding fields={fields} fieldsError={fieldsError} onSelect={setFieldId}/>;
  const code = fields.find(field => field.field_code === fieldId || String(field.field_id) === fieldId)?.field_code || fieldId;
  return <FieldSimulator key={code} fieldId={code}/>;
}
export default function SimulatorPage() { return <Suspense fallback={<p>Loading field...</p>}><Simulator/></Suspense>; }
