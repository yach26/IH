"use client";

import React, { Suspense } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, FileText, LoaderCircle, UploadCloud } from "lucide-react";
import {
  uploadSoilReport, confirmSoilReport, recommend, ApiError,
  type SoilReportUploadResponse, type SoilTestConfirmInput,
} from "@/lib/api";
import { useFieldParam } from "@/lib/useFieldParam";
import FieldSelector from "@/components/ui/FieldSelector";
import FieldOnboarding from "@/components/ui/FieldOnboarding";

const FIELDS = [
  { key: "n_kg_ha", label: "Nitrogen (N)", unit: "kg/ha", required: true, max: undefined },
  { key: "p_kg_ha", label: "Phosphorus", unit: "kg/ha", required: true, max: undefined },
  { key: "k_kg_ha", label: "Potassium", unit: "kg/ha", required: true, max: undefined },
  { key: "ph", label: "Soil pH", unit: "", required: false, max: 14 },
  { key: "oc_percent", label: "Organic carbon", unit: "%", required: false, max: 100 },
  { key: "ec_ds_m", label: "Electrical conductivity", unit: "dS/m", required: false, max: undefined },
] as const;
const ACCEPTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".pdf", ".txt", ".csv"];
const REVIEW_THRESHOLD = 0.85;
type EditableValues = Record<string, string>;

function today() {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

// Progress steps: upload → review → generating → done
type WorkflowStep = 1 | 2 | 3 | 4;

function UploadField() {
  const router = useRouter();
  const { fieldId, setFieldId, fields, fieldsError } = useFieldParam();
  const [dragActive, setDragActive] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [uploadResult, setUploadResult] = React.useState<SoilReportUploadResponse | null>(null);
  const [fileName, setFileName] = React.useState("");
  const [values, setValues] = React.useState<EditableValues>({});
  const [testDate, setTestDate] = React.useState("");
  const [pBasis, setPBasis] = React.useState<"" | "P" | "P2O5">("");
  const [kBasis, setKBasis] = React.useState<"" | "K" | "K2O">("");
  const [verified, setVerified] = React.useState(false);
  const [confirming, setConfirming] = React.useState(false);
  const [confirmError, setConfirmError] = React.useState<string | null>(null);
  const [saved, setSaved] = React.useState(false);
  const [generating, setGenerating] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const step: WorkflowStep = generating ? 3 : saved ? 2 : uploadResult ? 2 : 1;

  function resetForNewUpload() {
    setUploadResult(null); setUploadError(null); setValues({}); setTestDate("");
    setPBasis(""); setKBasis(""); setVerified(false); setSaved(false);
    setGenerating(false); setConfirmError(null); setFileName("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleFile(file: File) {
    if (!fieldId || uploading || confirming) return;
    resetForNewUpload();
    if (!ACCEPTED_EXTENSIONS.some((extension) => file.name.toLowerCase().endsWith(extension))) {
      setUploadError("Choose a supported image, PDF, TXT or CSV soil report."); return;
    }
    if (!file.size) {
      setUploadError("This file is empty. Choose a report containing the laboratory results."); return;
    }
    setFileName(file.name); setUploading(true);
    try {
      const result = await uploadSoilReport(fieldId, file);
      const initial: EditableValues = {};
      for (const { key } of FIELDS) {
        const value = result.extracted_data?.[key]?.value;
        initial[key] = value != null ? String(value) : "";
      }
      setValues(initial); setUploadResult(result);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed. Check the connection and try again.");
    } finally { setUploading(false); }
  }

  const validationErrors = FIELDS.flatMap(({ key, label, required, max }) => {
    const raw = values[key]?.trim() || "";
    if (!raw) return required ? [`Enter ${label.toLowerCase()} from the report.`] : [];
    const value = Number(raw);
    return !Number.isFinite(value) || value < 0 || (max !== undefined && value > max)
      ? [`${label} must be a valid number from 0${max !== undefined ? ` to ${max}` : " or higher"}.`] : [];
  });
  if (!testDate || !/^\d{4}-\d{2}-\d{2}$/.test(testDate) || !Number.isFinite(Date.parse(testDate)) || testDate > today()) {
    validationErrors.push("Enter the actual soil sample/test date from the report, no later than today.");
  }
  if (!pBasis || !kBasis) validationErrors.push("Confirm whether the report uses P or P₂O₅, and K or K₂O, in kg/ha.");
  const editedFields = FIELDS.filter(({ key }) => {
    const original = uploadResult?.extracted_data?.[key]?.value;
    const current = values[key]?.trim() || "";
    if (original == null || original === "") return current !== "";
    return current === "" || Number(original) !== Number(current);
  });

  async function handleConfirm() {
    if (confirming || !uploadResult || (!saved && (!verified || validationErrors.length))) return;
    setConfirming(true); setConfirmError(null);
    let hasSaved = saved;
    try {
      if (!hasSaved) {
        const soilTest: SoilTestConfirmInput = {
          source: uploadResult.status === "OCR_FAILED" ? "manual" : "ocr", test_date: testDate,
          p_basis: pBasis as "P" | "P2O5", k_basis: kBasis as "K" | "K2O",
        };
        for (const { key } of FIELDS) {
          const raw = values[key]?.trim();
          soilTest[key] = raw ? Number(raw) : null;
        }
        await confirmSoilReport(fieldId, { upload_id: uploadResult.upload_id, soil_test: soilTest });
        hasSaved = true; setSaved(true);
      }
      // Auto-generate recommendation after confirm
      setConfirming(false);
      setGenerating(true);
      try {
        await recommend(fieldId);
      } catch {
        // Even if recommend fails or returns ABSTAIN, navigate to report —
        // the report page handles ABSTAIN and error states gracefully.
      }
      router.push(`/report?field=${encodeURIComponent(fieldId)}`);
    } catch (err) {
      const detail = err instanceof ApiError ? err.message : "Check the connection and try again.";
      setConfirmError(hasSaved ? `Your soil record was saved, but the recommendation could not be generated. ${detail}` : detail);
      setConfirming(false);
      setGenerating(false);
    }
  }

  const needsReview = new Set(uploadResult?.fields_needing_review || []);
  const progressLabels: [string, string, string, string] = [
    "Upload report", "Review and confirm", "Generating plan", "View report"
  ];
  const currentStep = generating ? 3 : saved ? 2 : uploadResult ? 2 : 1;

  return (
    <div className="min-h-screen bg-background font-sans">
      <div className="sticky top-0 z-30 bg-surface border-b border-border px-4 md:px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-primary mb-1">Kisan Saathi · Soil report</p>
            <h1 className="font-serif text-xl font-bold text-foreground">Upload and verify your soil test</h1>
          </div>
          {fields.length > 0 ? <FieldSelector fieldId={fieldId} fields={fields} onChange={setFieldId} /> : (
            <span className="text-xs text-muted">{fieldsError ? `Field list unavailable (${fieldsError})` : "Loading fields…"}</span>
          )}
        </div>
      </div>
      <div className="max-w-3xl mx-auto px-4 md:px-6 py-8">
        <ol aria-label="Soil report progress" className="grid grid-cols-4 gap-2 mb-6 text-xs">
          {progressLabels.map((label, index) => (
            <li key={label} aria-current={currentStep === index + 1 ? "step" : undefined} className={`border-t-4 pt-3 ${currentStep >= index + 1 ? "border-primary text-primary font-semibold" : "border-border text-muted"}`}>
              {index + 1}. {label}
            </li>
          ))}
        </ol>

        {/* Generating plan state */}
        {generating && (
          <div role="status" aria-live="polite" className="bg-surface gov-panel border border-border shadow-sm p-10 text-center">
            <LoaderCircle aria-hidden="true" className="w-10 h-10 mx-auto text-primary animate-spin mb-4" />
            <h2 className="font-serif text-lg font-bold text-foreground mb-2">Generating fertilizer plan…</h2>
            <p className="text-sm text-muted">Running the recommendation pipeline for {fieldId}. You will be redirected to your report automatically.</p>
          </div>
        )}

        {!uploadResult && !generating && (
          <div onDragOver={(event) => { event.preventDefault(); if (!uploading) setDragActive(true); }} onDragLeave={() => setDragActive(false)} onDrop={(event) => {
            event.preventDefault(); setDragActive(false);
            const file = event.dataTransfer.files?.[0]; if (file) void handleFile(file);
          }} className={`bg-surface border-2 border-dashed gov-panel p-6 sm:p-12 text-center transition-colors ${dragActive ? "border-primary bg-primary/5" : "border-border"}`}>
            <input ref={fileInputRef} type="file" accept={ACCEPTED_EXTENSIONS.join(",")} className="sr-only" tabIndex={-1} aria-label="Choose soil report" disabled={uploading} onChange={(event) => {
              const file = event.target.files?.[0]; if (file) void handleFile(file);
            }} />
            <UploadCloud aria-hidden="true" className="w-10 h-10 text-primary mx-auto mb-3" />
            <p className="text-sm font-semibold text-foreground mb-2">Drag and drop your soil health card or laboratory report</p>
            <p className="text-xs text-muted leading-relaxed">PNG, JPG, JPEG, WEBP, BMP, TIFF, PDF, TXT or CSV</p>
            <button type="button" disabled={uploading} onClick={() => fileInputRef.current?.click()} className="mt-5 min-h-11 px-5 py-2 bg-primary hover:bg-primary-hover text-white text-sm font-semibold rounded-lg disabled:opacity-50">Choose report</button>
            {uploading && <div role="status" aria-live="polite" className="mt-5 text-sm text-muted">
              <div role="progressbar" aria-label="Uploading and reading soil report" aria-valuetext="Processing; review will be available when extraction finishes" className="flex justify-center items-center gap-2"><LoaderCircle aria-hidden="true" className="w-4 h-4 animate-spin" /> Uploading and reading report…</div>
              <p className="mt-2 text-xs break-all">{fileName}</p>
            </div>}
          </div>
        )}
        {uploadError && <p role="alert" className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm gov-panel p-4">{uploadError}</p>}
        {uploadResult && !generating && (
          <div className="bg-surface gov-panel border border-border shadow-sm p-4 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
              <div className="min-w-0"><h2 className="text-base font-bold text-foreground flex gap-2 items-center"><FileText aria-hidden="true" className="h-4 w-4" /> Review extracted values</h2><p className="text-xs text-muted mt-1 break-all">{fileName}</p></div>
              <button type="button" disabled={confirming || saved} onClick={resetForNewUpload} className="min-h-11 text-xs font-medium text-primary underline disabled:opacity-50">Use a different report</button>
            </div>
            <div className="mb-5 bg-amber-50 border border-amber-200 text-amber-900 text-sm rounded-lg p-4">
              <p className="font-semibold">Provisional values — farmer verification required</p>
              <p className="mt-1 leading-relaxed">{uploadResult.status === "OCR_FAILED" ? "The report could not be read. Enter the laboratory values below manually." : "OCR can misread numbers and units. Compare every value with your original report, including values marked high confidence."} These values enter your soil record only after you confirm.</p>
            </div>
            <fieldset disabled={confirming || saved} className="space-y-5 disabled:opacity-70">
              <legend className="sr-only">Soil test values and units</legend>
              {FIELDS.map(({ key, label, unit, required, max }) => {
                const extracted = uploadResult.extracted_data?.[key];
                const hasConfidence = extracted?.value != null && Number.isFinite(extracted.confidence);
                const flagged = needsReview.has(key) || !hasConfidence || extracted.confidence < REVIEW_THRESHOLD;
                const confidence = hasConfidence ? Math.round(Math.max(0, Math.min(1, extracted.confidence)) * 100) : null;
                const basis = key === "p_kg_ha" ? pBasis : key === "k_kg_ha" ? kBasis : "";
                return <div key={key}>
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <label htmlFor={`soil-${key}`} className="text-sm font-medium text-foreground">{label}{basis ? ` (${basis})` : ""}{unit ? ` · ${unit}` : ""}{required ? " *" : " (optional)"}</label>
                    <span className={`text-[11px] font-semibold px-2 py-1 rounded-full border ${flagged ? "bg-amber-50 text-amber-900 border-amber-200" : "bg-green-50 text-green-800 border-green-200"}`}>{confidence === null ? "Not detected · enter from report" : `${flagged ? "Needs review" : "High confidence"} · ${confidence}%`}</span>
                  </div>
                  <input id={`soil-${key}`} type="number" inputMode="decimal" step="any" min={0} max={max} required={required} value={values[key] ?? ""} onChange={(event) => {
                    setValues((previous) => ({ ...previous, [key]: event.target.value })); setVerified(false); setConfirmError(null);
                  }} className={`w-full min-h-11 text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary ${flagged ? "border-amber-300 bg-amber-50/30" : "border-border"}`} placeholder="Enter the value on your report" />
                </div>;
              })}
              <div className="grid sm:grid-cols-2 gap-4">
                <div><label htmlFor="soil-p-basis" className="text-sm font-medium block mb-2">Phosphorus basis on report *</label><select id="soil-p-basis" required value={pBasis} onChange={(event) => { setPBasis(event.target.value as typeof pBasis); setVerified(false); }} className="w-full min-h-11 text-sm border border-border rounded-lg px-3 py-2"><option value="">Check report and select</option><option value="P">Elemental P (kg/ha)</option><option value="P2O5">P₂O₅ (kg/ha)</option></select></div>
                <div><label htmlFor="soil-k-basis" className="text-sm font-medium block mb-2">Potassium basis on report *</label><select id="soil-k-basis" required value={kBasis} onChange={(event) => { setKBasis(event.target.value as typeof kBasis); setVerified(false); }} className="w-full min-h-11 text-sm border border-border rounded-lg px-3 py-2"><option value="">Check report and select</option><option value="K">Elemental K (kg/ha)</option><option value="K2O">K₂O (kg/ha)</option></select></div>
              </div>
              <p className="text-xs text-muted leading-relaxed">Use kg/ha as printed on the report. If it uses ppm, mg/kg or another unit, ask the laboratory for kg/ha values. Do not copy those numbers directly. Oxide values are converted by Kisan Saathi after confirmation.</p>
              <div><label htmlFor="soil-test-date" className="text-sm font-medium block mb-2">Soil sample / test date on report *</label><input id="soil-test-date" type="date" required max={today()} value={testDate} onChange={(event) => { setTestDate(event.target.value); setVerified(false); }} className="w-full min-h-11 text-sm border border-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary" /><p className="text-xs text-muted mt-2">Use the actual sample or test date, which may differ from the upload date.</p></div>
            </fieldset>
            <div className="mt-6 bg-background border border-border rounded-lg p-4">
              <h3 className="text-sm font-semibold">Review summary</h3>
              <p className="text-xs text-muted mt-1">{editedFields.length ? `${editedFields.length} value${editedFields.length === 1 ? "" : "s"} edited or added since extraction.` : "No numeric values changed since extraction."} Confirming records these values for {fieldId}.</p>
              {editedFields.length > 0 && <ul className="mt-3 space-y-1 text-xs text-foreground">{editedFields.map(({ key, label, unit }) => <li key={key}>{label}: {String(uploadResult.extracted_data?.[key]?.value ?? "not detected")} → {values[key]?.trim() || "not provided"}{unit ? ` ${unit}` : ""}</li>)}</ul>}
              <p className="text-xs mt-3">Sample/test date: {testDate || "Required"} · P basis: {pBasis || "Required"} · K basis: {kBasis || "Required"}</p>
            </div>
            {!saved && validationErrors.length > 0 && <div className="mt-4 text-sm text-amber-900"><p className="font-semibold">What we need next</p><ul className="list-disc pl-5 mt-2 space-y-1">{validationErrors.map((error) => <li key={error}>{error}</li>)}</ul></div>}
            <label className="flex gap-3 items-start min-h-11 mt-5 p-3 border border-border rounded-lg cursor-pointer"><input type="checkbox" checked={verified} disabled={confirming || saved} onChange={(event) => setVerified(event.target.checked)} className="mt-0.5 h-5 w-5 shrink-0 accent-primary" /><span className="text-sm"><span className="font-semibold">I have verified these values</span><span className="block text-xs text-muted mt-1">I checked every value, the kg/ha units, nutrient basis and sample/test date against my report.</span></span></label>
            {confirmError && <p role="alert" className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg p-3">{confirmError}</p>}
            <button type="button" onClick={() => void handleConfirm()} disabled={confirming || (!saved && (!verified || validationErrors.length > 0))} className="mt-5 w-full min-h-12 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white text-sm font-semibold px-5 py-3 rounded-lg transition flex items-center justify-center gap-2">
              {confirming && <LoaderCircle aria-hidden="true" className="w-4 h-4 animate-spin" />}{confirming ? (saved ? "Refreshing field…" : "Saving verified values…") : saved ? "Retry field refresh" : "Confirm and update field"}
            </button>
            <p className="text-xs text-muted mt-3 text-center">After confirming, Kisan Saathi will automatically generate your fertilizer plan and open your field report.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function UploadContent() {
  const { fieldId, setFieldId, fields, fieldsError } = useFieldParam();
  if (!fieldId) return <FieldOnboarding fields={fields} fieldsError={fieldsError} onSelect={setFieldId} />;
  return <UploadField key={fieldId} />;
}

export default function UploadPage() {
  return <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center text-sm text-muted">Loading…</div>}><UploadContent /></Suspense>;
}
