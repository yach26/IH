"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getAuthHeaders } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FieldSummary {
  id: number;
  code: string;
  crop?: string;
}

interface ExtractedData {
  [key: string]: { value: number | null; confidence: number } | undefined;
}

function UploadContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<string>(
    searchParams.get("field") || ""
  );
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<{
    upload_id?: number;
    engine?: string;
    extracted_data?: ExtractedData;
    fields_needing_review?: string[];
  } | null>(null);
  const [confirmValues, setConfirmValues] = useState({
    n_kg_ha: "",
    p_kg_ha: "",
    k_kg_ha: "",
    ph: "",
    oc_percent: "",
    ec_ds_m: "",
    test_date: new Date().toISOString().split("T")[0],
  });
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadFields();
  }, []);

  const loadFields = async () => {
    try {
      const res = await fetch(`${API_BASE}/fields`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setFields(data.fields || []);
        if (!selectedFieldId && data.fields?.length > 0) {
          setSelectedFieldId(String(data.fields[0].id));
        }
      }
    } catch (e) {
      console.error("Failed to load fields", e);
    }
  };

  const handleUpload = async () => {
    if (!file || !selectedFieldId) return;
    setLoading(true);
    setMessage("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(
        `${API_BASE}/fields/${selectedFieldId}/soil-report/upload`,
        { method: "POST", body: formData, headers: getAuthHeaders() }
      );
      if (res.ok) {
        const data = await res.json();
        setUploadResult(data);
        if (data.extracted_data) {
          const vals: Record<string, string> = {};
          for (const [k, v] of Object.entries(data.extracted_data)) {
            const entry = v as { value?: number | null } | undefined;
            if (entry?.value != null) vals[k] = String(entry.value);
          }
          setConfirmValues((prev) => ({ ...prev, ...vals }));
        }
        setMessage("OCR extraction complete. Review values below.");
      } else {
        setMessage("Upload failed. You can enter values manually below.");
      }
    } catch (e) {
      setMessage("Upload error. You can enter values manually below.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!selectedFieldId) return;
    setLoading(true);
    setMessage("");
    try {
      const payload = {
        upload_id: uploadResult?.upload_id,
        soil_test: {
          n_kg_ha: parseFloat(confirmValues.n_kg_ha) || 0,
          p_kg_ha: parseFloat(confirmValues.p_kg_ha) || 0,
          k_kg_ha: parseFloat(confirmValues.k_kg_ha) || 0,
          ph: parseFloat(confirmValues.ph) || 7.0,
          oc_percent: parseFloat(confirmValues.oc_percent) || 0,
          ec_ds_m: parseFloat(confirmValues.ec_ds_m) || 0,
          test_date: confirmValues.test_date,
          source: uploadResult?.upload_id ? "ocr" : "manual",
        },
      };
      const res = await fetch(
        `${API_BASE}/fields/${selectedFieldId}/soil-report/confirm`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", ...getAuthHeaders() },
          body: JSON.stringify(payload),
        }
      );
      if (res.ok) {
        setMessage("Soil report confirmed! Twin updated.");
        setTimeout(() => {
          router.push(`/dashboard?field=${selectedFieldId}`);
        }, 1500);
      } else {
        const err = await res.json().catch(() => ({}));
        setMessage(err.detail || "Confirmation failed");
      }
    } catch (e) {
      setMessage("Error confirming soil report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-light">
      <header className="bg-white border-b border-border sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="text-lg font-bold text-ink-primary">Upload Soil Report</span>
          <a href={`/dashboard?field=${selectedFieldId}`} className="btn-secondary text-xs">
            Back to Dashboard
          </a>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {message && (
          <div className={`p-4 rounded-lg text-sm ${
            message.includes("confirmed") || message.includes("complete")
              ? "bg-green-50 border border-green-200 text-green-700"
              : "bg-amber-50 border border-amber-200 text-amber-700"
          }`}>
            {message}
          </div>
        )}

        {/* Field Selector */}
        <div className="card-clean">
          <label className="text-xs font-semibold text-ink-secondary block mb-2">Select Field</label>
          <select
            value={selectedFieldId}
            onChange={(e) => setSelectedFieldId(e.target.value)}
            className="input-clean"
          >
            {fields.map((f) => (
              <option key={f.id} value={f.id}>
                {f.code} {f.crop ? `(${f.crop})` : ""}
              </option>
            ))}
          </select>
        </div>

        {/* File Upload */}
        <div className="card-clean">
          <h3 className="text-base font-bold text-ink-primary mb-4">Upload Soil Health Card</h3>
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition ${
              dragOver ? "border-agri-primary bg-agri-light" : "border-border"
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const f = e.dataTransfer.files?.[0];
              if (f) setFile(f);
            }}
          >
            <input
              type="file"
              id="soil-file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
              accept=".txt,.pdf,.csv,.png,.jpg,.jpeg,.webp"
            />
            <label htmlFor="soil-file" className="cursor-pointer inline-flex flex-col items-center">
              <span className="text-3xl mb-2">&#128196;</span>
              <span className="btn-secondary text-xs mb-2">Choose File</span>
              <span className="text-xs text-ink-muted">
                {file ? file.name : "PNG, JPG, PDF, TXT, CSV"}
              </span>
            </label>
          </div>
          {file && (
            <div className="mt-4">
              <button onClick={handleUpload} disabled={loading} className="btn-primary text-sm">
                {loading ? "Extracting..." : "Upload & Run OCR"}
              </button>
            </div>
          )}
        </div>

        {/* Extracted Values / Manual Entry */}
        <div className="card-clean">
          <h3 className="text-base font-bold text-ink-primary mb-4">
            Soil Test Values
            {uploadResult?.fields_needing_review && uploadResult.fields_needing_review.length > 0 && (
              <span className="badge badge-medium ml-2">Review Required</span>
            )}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { key: "n_kg_ha", label: "Nitrogen (kg/ha)" },
              { key: "p_kg_ha", label: "Phosphorus (kg/ha)" },
              { key: "k_kg_ha", label: "Potassium (kg/ha)" },
              { key: "ph", label: "pH" },
              { key: "oc_percent", label: "Organic Carbon (%)" },
              { key: "ec_ds_m", label: "EC (dS/m)" },
            ].map(({ key, label }) => (
              <div key={key}>
                <label className="text-xs font-semibold text-ink-secondary block mb-1">
                  {label}
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={confirmValues[key as keyof typeof confirmValues] as string}
                  onChange={(e) =>
                    setConfirmValues({ ...confirmValues, [key]: e.target.value })
                  }
                  className="input-clean"
                />
                {uploadResult?.extracted_data?.[key]?.confidence != null && (
                  <span className="text-[10px] text-ink-muted mt-1 block">
                    OCR Confidence: {uploadResult.extracted_data[key]!.confidence}
                  </span>
                )}
              </div>
            ))}
            <div>
              <label className="text-xs font-semibold text-ink-secondary block mb-1">
                Test Date
              </label>
              <input
                type="date"
                value={confirmValues.test_date}
                onChange={(e) =>
                  setConfirmValues({ ...confirmValues, test_date: e.target.value })
                }
                className="input-clean"
              />
            </div>
          </div>
          <div className="pt-4 flex justify-end gap-3">
            <button
              onClick={() => {
                setUploadResult(null);
                setConfirmValues({
                  n_kg_ha: "", p_kg_ha: "", k_kg_ha: "",
                  ph: "", oc_percent: "", ec_ds_m: "",
                  test_date: new Date().toISOString().split("T")[0],
                });
              }}
              className="btn-secondary"
            >
              Clear
            </button>
            <button onClick={handleConfirm} disabled={loading} className="btn-primary">
              {loading ? "Updating Twin..." : "Confirm & Update Digital Twin"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function UploadPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
          <p className="text-sm text-ink-secondary">Loading...</p>
        </div>
      </div>
    }>
      <UploadContent />
    </Suspense>
  );
}
