"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { assignCrop, createFarmer, createField, getOnboardingOptions, type FieldSummary, type OnboardingOptions } from "@/lib/api";

export default function FieldOnboarding({ fields, fieldsError, onSelect }: {
  fields: FieldSummary[]; fieldsError: string | null; onSelect: (id: string) => void;
}) {
  const router = useRouter();
  const [options, setOptions] = useState<OnboardingOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const [farmerId, setFarmerId] = useState<number | null>(null);
  const [fieldId, setFieldId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [districtId, setDistrictId] = useState("");
  const [cropIndex, setCropIndex] = useState("");
  const [area, setArea] = useState("");
  const [irrigation, setIrrigation] = useState("");
  const [sowingDate, setSowingDate] = useState("");
  const [stage, setStage] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");

  useEffect(() => {
    let active = true;
    getOnboardingOptions().then(data => { if (active) { setOptions(data); setError(null); } })
      .catch(err => { if (active) setError(err instanceof Error ? err.message : "Could not load field options."); });
    return () => { active = false; };
  }, [retry]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const district = options?.districts.find(d => String(d.district_id) === districtId);
    const crop = cropIndex !== "" ? options?.crops[Number(cropIndex)] : undefined;
    if (!district || !crop) return;
    if ((lat === "") !== (lon === "")) { setError("Enter both latitude and longitude, or leave both blank."); return; }
    setBusy(true);
    setError(null);
    try {
      const farmer = farmerId ?? (await createFarmer({ region_id: district.region_id, full_name: name.trim() })).farmer_id;
      setFarmerId(farmer);
      const field = fieldId ?? (await createField({
        region_id: district.region_id, district_id: district.district_id, farmer_id: farmer,
        field_code: `FARM-${crypto.randomUUID()}`, area_ha: Number(area), irrigation_type: irrigation,
        lat: lat === "" ? null : Number(lat), lon: lon === "" ? null : Number(lon),
      })).field_id;
      setFieldId(field);
      await assignCrop(String(field), { crop_code: crop.crop_code, recommendation_type: crop.recommendation_type, sowing_date: sowingDate, current_stage: stage || null });
      router.push(`/upload?field=${field}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save your field. Please retry.");
      setBusy(false);
    }
  }

  const input = "mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm disabled:bg-gray-100";
  const selectedCrop = cropIndex === "" ? null : options?.crops[Number(cropIndex)];
  const region = options?.districts.find(d => String(d.district_id) === districtId)?.region_id;
  const stages = [...new Set(options?.stages.filter(s => s.crop_code === selectedCrop?.crop_code && (s.region_id === null || s.region_id === region)).map(s => s.stage_name) || [])];
  return (
    <main className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto max-w-2xl rounded-2xl border border-gray-200 bg-white p-6 md:p-8">
        <p className="text-xs font-semibold uppercase tracking-widest text-green-800">Step 1 of 3 · Your field</p>
        <h1 className="mt-3 text-2xl font-bold text-gray-900">Tell us about your farm</h1>
        <p className="mt-2 text-sm text-gray-600">Add your field details, upload your Soil Health Card, then review and confirm the extracted values. Your dashboard will use that confirmed data.</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <fieldset disabled={busy || farmerId !== null} className="space-y-4">
            <label className="block text-sm font-medium">Farmer name<input className={input} required value={name} onChange={e => setName(e.target.value)} /></label>
            <label className="block text-sm font-medium">District and state<select required className={input} value={districtId} onChange={e => setDistrictId(e.target.value)}>
              <option value="">Select your location</option>
              {options?.districts.map(d => <option key={d.district_id} value={d.district_id}>{d.district_name}, {d.region_name}</option>)}
            </select></label>
          </fieldset>
          <fieldset disabled={busy || fieldId !== null} className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-medium">Field area (hectares)<input required type="number" min="0.01" step="any" className={input} value={area} onChange={e => setArea(e.target.value)} /></label>
            <label className="text-sm font-medium">Irrigation<select required className={input} value={irrigation} onChange={e => setIrrigation(e.target.value)}><option value="">Select irrigation</option><option>Irrigated</option><option>Rainfed</option></select></label>
            <label className="text-sm font-medium">Latitude (optional)<input type="number" min="-90" max="90" step="any" className={input} value={lat} onChange={e => setLat(e.target.value)} /></label>
            <label className="text-sm font-medium">Longitude (optional)<input type="number" min="-180" max="180" step="any" className={input} value={lon} onChange={e => setLon(e.target.value)} /></label>
          </fieldset>
          <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-medium">Crop and season<select required className={input} value={cropIndex} onChange={e => { setCropIndex(e.target.value); setStage(""); }}><option value="">Select your crop</option>{options?.crops.map((c, i) => <option key={`${c.crop_code}-${c.recommendation_type}`} value={i}>{c.crop_name} · {c.recommendation_type.replaceAll("_", " ").toLowerCase()}</option>)}</select></label>
            <label className="text-sm font-medium">Current crop stage<select required={stages.length > 0} className={input} value={stage} onChange={e => setStage(e.target.value)}><option value="">{stages.length ? "Select current stage" : "No supported stages available"}</option>{stages.map(s => <option key={s} value={s}>{s.replaceAll("_", " ").toLowerCase()}</option>)}</select></label>
            <label className="text-sm font-medium">Sowing date<input required type="date" className={input} value={sowingDate} onChange={e => setSowingDate(e.target.value)} /></label>
          </fieldset>
          <p className="text-xs text-gray-500">Only currently supported locations and crop seasons are listed. Leave coordinates blank if you do not know them.</p>
          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          {!options && <button type="button" className="text-sm underline" onClick={() => setRetry(r => r + 1)}>Reload available options</button>}
          {fieldId !== null && <p className="text-xs text-gray-600">Your field has been saved. Retry to finish its crop details.</p>}
          <button disabled={busy || !options} className="w-full rounded-lg bg-[#0F4D35] px-5 py-3 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Saving your field…" : "Save field & upload soil report"}</button>
        </form>
        <details className="mt-6 border-t border-gray-200 pt-4">
          <summary className="cursor-pointer text-sm font-medium text-gray-600">Open an existing farmer field</summary>
          <p className="mt-2 text-xs text-gray-500">Select a field previously created through farmer onboarding.</p>
          <select aria-label="Open an existing field" value="" className={input} onChange={e => { if (e.target.value) onSelect(e.target.value); }}>
            <option value="">Choose a field</option>
            {fields.map(f => <option key={f.field_code} value={f.field_code}>{f.field_code} · {f.farmer_name || f.crop_code || "Unassigned"}</option>)}
          </select>
          {fieldsError && <p role="alert" className="mt-2 text-xs text-red-700">{fieldsError}</p>}
        </details>
        <Link href="/demo" className="mt-5 inline-block text-sm underline text-gray-600">View separate pilot demo (sample data)</Link>
      </div>
    </main>
  );
}
