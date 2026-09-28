"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getFields, type FieldSummary } from "@/lib/api";
export default function DemoPage() {
  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let cancelled = false;
    getFields(true).then(rows => { if (!cancelled) { setFields(rows); setLoaded(true); } })
      .catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : "Could not load pilot records"); });
    return () => { cancelled = true; };
  }, []);
  return <main className="mx-auto max-w-4xl p-6 space-y-5">
    <h1 className="text-3xl font-bold">Pilot demo ? sample data</h1>
    <p>These preloaded records demonstrate the app. They are not your farm or your uploaded soil results. This view is read-only.</p>
    <Link href="/dashboard" className="inline-block rounded bg-primary px-4 py-3 text-white">Set up my own field</Link>
    {error && <p role="alert">{error}</p>}
    {!loaded && !error && <p>Loading pilot examples?</p>}
    {loaded && !fields.length && <p>No pilot examples available.</p>}
    <div className="grid gap-4 sm:grid-cols-2">{fields.map(field => <article key={field.field_code} className="rounded-xl border p-5">
      <p className="text-xs font-semibold uppercase">Sample record</p><h2 className="font-bold">{field.field_code}</h2>
      <p>{field.crop_code || "Crop unassigned"}</p>
      <p>Sample soil score: {field.soil_health_score == null ? "Unavailable" : `${Math.round(field.soil_health_score)}/100`}</p>
    </article>)}</div>
  </main>;
}
