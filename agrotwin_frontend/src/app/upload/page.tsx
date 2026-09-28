"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import {
  uploadSoilReport,
  confirmSoilReport,
  getTwin,
  ApiError,
  type SoilReportUploadResponse,
} from "@/lib/api";
import { useFieldParam } from "@/lib/useFieldParam";
import FieldSelector from "@/components/ui/FieldSelector";
import FieldOnboarding from "@/components/ui/FieldOnboarding";

const FIELD_LABELS: Record<string, string> = {
  n_kg_ha: "Nitrogen (N) kg/ha",
  p_kg_ha: "Phosphorus (P) kg/ha",
  k_kg_ha: "Potassium (K) kg/ha",
  ph: "Soil pH",
  oc_percent: "Organic Carbon (OC) %",
  ec_ds_m: "Electrical Conductivity (EC) dS/m",
};

const REVIEW_THRESHOLD = 0.85;

type EditableValues = Record<string, string>;

function UploadField() {
  const { fieldId, setFieldId, fields, fieldsError } = useFieldParam();

  const [dragActive, setDragActive] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [uploadResult, setUploadResult] = React.useState<SoilReportUploadResponse | null>(null);
  const [values, setValues] = React.useState<EditableValues>({});
  const [testDate, setTestDate] = React.useState<string>(new Date().toISOString().slice(0, 10));

  const [confirming, setConfirming] = React.useState(false);
  const [confirmError, setConfirmError] = React.useState<string | null>(null);
  const [confirmed, setConfirmed] = React.useState(false);

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  function resetForNewUpload() {
    setUploadResult(null);
    setUploadError(null);
    setValues({});
    setConfirmed(false);
    setConfirmError(null);
  }

  async function handleFile(file: File) {
    if (!fieldId || uploading || confirming) return;
    resetForNewUpload();
    setUploading(true);
    try {
      const result = await uploadSoilReport(fieldId, file);
      setUploadResult(result);
      const initial: EditableValues = {};
      for (const [key, field] of Object.entries(result.extracted_data || {})) {
        initial[key] = field.value != null ? String(field.value) : "";
      }
      setValues(initial);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed — the backend may be unreachable.");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  async function handleConfirm() {
    setConfirming(true);
    setConfirmError(null);
    try {
      const soil_test: Record<string, number | string | null> = { source: "ocr", test_date: testDate };
      for (const key of Object.keys(FIELD_LABELS)) {
        const raw = values[key];
        soil_test[key] = raw === "" || raw === undefined ? null : Number(raw);
      }
      await confirmSoilReport(fieldId, {
        upload_id: uploadResult?.upload_id ?? null,
        soil_test: soil_test as never,
      });
      await getTwin(fieldId);
      setConfirmed(true);
    } catch (err) {
      setConfirmError(err instanceof ApiError ? err.message : "Confirm failed — the backend may be unreachable.");
    } finally {
      setConfirming(false);
    }
  }

  const needsReview = new Set(uploadResult?.fields_needing_review || []);

  return (
    <div className="min-h-screen bg-background font-sans">
      <div className="bg-surface border-b border-border px-4 md:px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between gap-3 flex-wrap">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-primary mb-1">Soil Report OCR</p>
            <h1 className="font-serif text-xl font-bold text-foreground">Upload Soil Report</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted font-medium">Field:</span>
            {fields.length > 0 ? (
              <FieldSelector fieldId={fieldId} fields={fields} onChange={(f) => { setFieldId(f); resetForNewUpload(); }} />
            ) : (
              <span className="text-xs text-muted">{fieldsError ? `Field list unavailable (${fieldsError})` : "Loading fields…"}</span>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 md:px-6 py-8">
        {!uploadResult && (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`bg-surface border-2 border-dashed gov-panel p-12 text-center cursor-pointer transition-colors ${
              dragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,.pdf,.txt,.csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
            <div className="text-4xl mb-3">📄</div>
            <p className="text-sm font-semibold text-foreground mb-1">
              {uploading ? "Uploading and running OCR…" : "Drag & drop a soil health card, or click to browse"}
            </p>
            <p className="text-xs text-muted">Image (PNG/JPG) or PDF soil test report</p>
            {uploading && (
              <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted">
                <span className="inline-block w-3.5 h-3.5 border-2 border-border border-t-primary rounded-full animate-spin" />
                Extracting values…
              </div>
            )}
          </div>
        )}

        {uploadError && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 text-sm gov-panel p-4">
            {uploadError}
          </div>
        )}

        {uploadResult && !confirmed && (
          <div className="bg-surface gov-panel border border-border shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-foreground">Extracted values ({uploadResult.engine})</h2>
              <button
                onClick={resetForNewUpload}
                className="text-xs font-medium text-muted hover:text-primary"
              >
                Upload a different file
              </button>
            </div>

            {uploadResult.status === "OCR_FAILED" && (
              <div className="mb-4 bg-accent-bg border border-accent/30 text-accent text-xs gov-panel p-3">
                OCR could not read this file at all. Enter the values manually below before confirming —
                nothing has been saved to this field yet.
              </div>
            )}

            <div className="space-y-4">
              {Object.keys(FIELD_LABELS).map((key) => {
                const extracted = uploadResult.extracted_data?.[key];
                const flagged = needsReview.has(key);
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-medium text-foreground">{FIELD_LABELS[key]}</label>
                      {extracted && (
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                            flagged || extracted.confidence < REVIEW_THRESHOLD
                              ? "bg-accent-bg text-accent border-accent/30"
                              : "bg-green-50 text-green-700 border-green-200"
                          }`}
                        >
                          {flagged || extracted.confidence < REVIEW_THRESHOLD
                            ? `⚠ Needs review (${Math.round(extracted.confidence * 100)}%)`
                            : `✓ Confidence ${Math.round(extracted.confidence * 100)}%`}
                        </span>
                      )}
                    </div>
                    <input
                      type="number"
                      step="any"
                      value={values[key] ?? ""}
                      onChange={(e) => setValues((v) => ({ ...v, [key]: e.target.value }))}
                      className={`w-full text-sm border gov-panel px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary ${
                        flagged || (extracted && extracted.confidence < REVIEW_THRESHOLD)
                          ? "border-accent/40 bg-accent-bg/30"
                          : "border-border"
                      }`}
                      placeholder="Not detected — enter manually"
                    />
                  </div>
                );
              })}

              <div>
                <label className="text-xs font-medium text-foreground block mb-1">Test date</label>
                <input
                  type="date"
                  value={testDate}
                  onChange={(e) => setTestDate(e.target.value)}
                  className="w-full text-sm border border-border gov-panel px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <p className="text-[11px] text-muted mt-4">
              Nothing is written to this field&apos;s soil record until you confirm — low-confidence values are
              never auto-accepted.
            </p>

            {confirmError && (
              <div className="mt-3 bg-red-50 border border-red-200 text-red-700 text-xs gov-panel p-3">{confirmError}</div>
            )}

            <button
              onClick={handleConfirm}
              disabled={confirming || ["n_kg_ha", "p_kg_ha", "k_kg_ha"].some(key => !values[key]?.trim() || !Number.isFinite(Number(values[key])))}
              className="mt-5 w-full bg-primary hover:bg-primary-hover disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 gov-panel transition"
            >
              {confirming ? "Confirming…" : "Confirm & Update Field"}
            </button>
          </div>
        )}

        {confirmed && (
          <div className="bg-surface gov-panel border border-green-200 shadow-sm p-8 text-center">
            <div className="text-3xl mb-3">✅</div>
            <h2 className="font-serif text-lg font-bold text-foreground mb-2">Soil data updated</h2>
            <p className="text-sm text-muted mb-5">
              Field {fieldId}&apos;s soil test has been recorded and the digital twin will reflect it on next fetch.
            </p>
            <Link
              href={`/dashboard?field=${encodeURIComponent(fieldId)}`}
              className="inline-flex items-center gap-2 bg-primary hover:bg-primary-hover text-white text-sm font-semibold px-5 py-2.5 gov-panel transition"
            >
              View Dashboard
            </Link>
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
  return (
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center text-sm text-muted">Loading…</div>}>
      <UploadContent />
    </Suspense>
  );
}
