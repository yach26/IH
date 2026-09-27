"use client";

import type { FieldSummary } from "@/lib/api";

export default function FieldSelector({
  fieldId,
  fields,
  onChange,
  className = "",
}: {
  fieldId: string;
  fields: FieldSummary[];
  onChange: (fieldCode: string) => void;
  className?: string;
}) {
  return (
    <select
      value={fieldId}
      onChange={(e) => onChange(e.target.value)}
      className={`text-sm font-medium bg-white border border-gray-200 rounded-md px-3 py-1.5 cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#0F4D35] ${className}`}
    >
      {!fields.some((f) => f.field_code === fieldId) && (
        <option value={fieldId}>{fieldId}</option>
      )}
      {fields.map((f) => (
        <option key={f.field_code} value={f.field_code}>
          {f.field_code} — {f.crop_code || "Unassigned"}
        </option>
      ))}
    </select>
  );
}
