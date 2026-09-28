"use client";
import { useEffect, useState } from "react";
import { getApplications, getFertilizerProducts, recordApplication, type FertilizerApplication } from "@/lib/api";
export default function ApplicationHistory({ fieldId, onRecorded }: { fieldId: string; onRecorded?: () => void }) {
  const [rows, setRows] = useState<FertilizerApplication[]>([]);
  const [products, setProducts] = useState<{product_code: string; product_name: string}[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => {
    let cancelled = false;
    Promise.all([getApplications(fieldId), getFertilizerProducts()]).then(([history, catalog]) => {
      if (!cancelled) { setRows(history.applications); setProducts(catalog); setLoaded(true); }
    }).catch(err => { if (!cancelled) setError(String(err)); });
    return () => { cancelled = true; };
  }, [fieldId]);
  return <section className="rounded-xl border border-border bg-white p-5 space-y-3">
    <h2 className="text-lg font-bold">Previous fertilizer applications</h2>
    <p className="text-sm text-muted">Record what was actually applied. Recommendations are not proof of application. Missing history does not mean no fertilizer was used.</p>
    {!loaded && !error && <p className="text-sm text-muted">Loading application history...</p>}
    {loaded && !rows.length && <p className="text-sm text-muted">No applications recorded for this field.</p>}
    <ul className="space-y-1 text-sm">{rows.map(row => <li key={row.application_id} className="bg-surface p-2 rounded border border-border text-foreground">{row.application_date}: <span className="font-semibold">{row.product_code}</span>, {row.quantity_kg_ha} kg/ha</li>)}</ul>
    <form className="flex flex-wrap items-end gap-3" onSubmit={async event => {
      event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
      setBusy(true); setError(""); setMessage("");
      try {
        await recordApplication(fieldId, { product_code: String(data.get("product")), application_date: String(data.get("date")), quantity_kg_ha: Number(data.get("quantity")) });
        setMessage("Application saved. Any residual nutrient credit requires a supported policy; review may be required."); form.reset(); onRecorded?.();
        try { setRows((await getApplications(fieldId)).applications); } catch { setError("Application saved, but history could not refresh. Reload the page; do not submit it again."); }
      } catch (err) { setError(err instanceof Error ? err.message : "Application could not be saved."); }
      finally { setBusy(false); }
    }}>
      <label className="grid text-sm gap-1 flex-1 min-w-[190px]">Product<select name="product" required defaultValue="" className="border rounded p-2 text-sm bg-white text-foreground w-full"><option value="" disabled>Select product</option>{products.map(p => <option key={p.product_code} value={p.product_code}>{p.product_name.replace(/_/g, " ")}</option>)}</select></label>
      <label className="grid text-sm gap-1 flex-1 min-w-[130px]">Application date<input name="date" type="date" required className="border rounded p-2 text-sm bg-white text-foreground max-w-full" /></label>
      <label className="grid text-sm gap-1 flex-1 min-w-[100px]">Quantity (kg/ha)<input name="quantity" type="number" min="0.01" step="any" required className="border rounded p-2 text-sm bg-white text-foreground max-w-full" /></label>
      <button disabled={busy || !loaded} className="bg-primary text-white font-medium text-sm rounded px-4 py-2 min-h-[40px] w-full sm:w-auto disabled:opacity-50">{busy ? "Saving..." : "Record application"}</button>
    </form>
    {error && <p role="alert" className="text-sm text-red-600 font-medium">{error}</p>}{message && <p role="status" className="text-sm text-green-700 font-medium">{message}</p>}
  </section>;
}
