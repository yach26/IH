"use client";
import { useEffect, useState } from "react";
import { getApplications, getFertilizerProducts, recordApplication, type FertilizerApplication } from "@/lib/api";
import LocalizedText from "@/components/ui/LocalizedText";
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
  return <LocalizedText><section className="rounded-xl border border-border bg-white p-5 space-y-3">
    <h2 className="text-lg font-bold">Previous fertilizer applications</h2>
    <p className="text-sm text-muted">Record what was actually applied. Recommendations are not proof of application. Missing history does not mean no fertilizer was used.</p>
    {!loaded && !error && <p>Loading application history?</p>}
    {loaded && !rows.length && <p>No applications recorded for this field.</p>}
    <ul>{rows.map(row => <li key={row.application_id}>{row.application_date}: {row.product_code}, {row.quantity_kg_ha} kg/ha</li>)}</ul>
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
      <label className="grid text-sm gap-1">Product<select name="product" required defaultValue="" className="border rounded p-2"><option value="" disabled>Select product</option>{products.map(p => <option key={p.product_code} value={p.product_code}>{p.product_name}</option>)}</select></label>
      <label className="grid text-sm gap-1">Application date<input name="date" type="date" required className="border rounded p-2" /></label>
      <label className="grid text-sm gap-1">Quantity (kg/ha)<input name="quantity" type="number" min="0.01" step="any" required className="border rounded p-2 w-32" /></label>
      <button disabled={busy || !loaded} className="bg-primary text-white rounded px-4 py-2 disabled:opacity-50">{busy ? "Saving?" : "Record application"}</button>
    </form>
    {error && <p role="alert">{error}</p>}{message && <p role="status">{message}</p>}
  </section></LocalizedText>;
}
