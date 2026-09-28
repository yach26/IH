"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Check, ChevronDown, Sprout, Wheat } from "lucide-react";
import { fieldDisplayName, type FieldSummary } from "@/lib/api";

function CropIcon({ crop }: { crop?: string | null }) {
  const Icon = crop && /rice|wheat|maize|paddy|jowar|bajra/i.test(crop) ? Wheat : Sprout;
  return <Icon aria-hidden="true" className="h-4 w-4 shrink-0 text-primary" />;
}

function SoilScore({ score }: { score?: number | null }) {
  const available = typeof score === "number" && Number.isFinite(score);
  return <span className={`shrink-0 rounded-full border px-2 py-1 text-[10px] font-semibold ${available ? "border-green-200 bg-green-50 text-green-800" : "border-border bg-background text-muted"}`}>
    {available ? `Soil ${Math.round(score)}/100` : "Soil score unavailable"}
  </span>;
}

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
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const optionRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const listId = useId();
  const selected = fields.find((field) => field.field_code === fieldId);

  useEffect(() => {
    if (!open) return;
    optionRefs.current[Math.max(0, fields.findIndex((field) => field.field_code === fieldId))]?.focus();
    function onOutsideClick(event: PointerEvent) {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("pointerdown", onOutsideClick);
    return () => document.removeEventListener("pointerdown", onOutsideClick);
  }, [open, fieldId, fields]);

  function close() {
    setOpen(false);
    trigger.current?.focus();
  }

  return (
    <div ref={container} className={`relative min-w-0 max-w-full ${className}`} onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget as Node)) setOpen(false);
    }}
    >
      <button ref={trigger} type="button" aria-label={`Select field. Current field: ${fieldId || "none"}`} aria-haspopup="listbox" aria-expanded={open} aria-controls={open ? listId : undefined}
        onClick={() => setOpen((previous) => !previous)} onKeyDown={(event) => {
          if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); setOpen(true); }
          if (event.key === "Escape") close();
        }} className="flex items-center gap-2 min-h-11 max-w-full rounded-lg border border-border bg-white px-3 py-2 text-left focus:outline-none focus:ring-2 focus:ring-primary">
        <CropIcon crop={selected?.crop_code} />
        <span className="min-w-0"><span className="block truncate text-xs font-semibold text-foreground">{selected ? fieldDisplayName(selected.field_code, selected.field_id) : (fieldId || "Select field")}</span><span className="block text-[10px] text-muted">{selected?.crop_code || "Crop unassigned"}</span></span>
        <SoilScore score={selected?.soil_health_score} />
        <ChevronDown aria-hidden="true" className="h-4 w-4 shrink-0 text-muted" />
      </button>
      {open && <div id={listId} role="listbox" aria-label="Fields" className="absolute top-full right-0 z-50 mt-2 w-80 max-w-[calc(100vw-2rem)] max-h-80 overflow-y-auto rounded-xl border border-border bg-white p-1 shadow-lg">
        {fields.map((field, index) => <button key={field.field_code} ref={(element) => { optionRefs.current[index] = element; }} type="button" role="option" aria-selected={field.field_code === fieldId} tabIndex={-1}
          onKeyDown={(event) => {
            let next = index;
            if (event.key === "ArrowDown") next = (index + 1) % fields.length;
            else if (event.key === "ArrowUp") next = (index - 1 + fields.length) % fields.length;
            else if (event.key === "Home") next = 0;
            else if (event.key === "End") next = fields.length - 1;
            else if (event.key === "Escape") { event.preventDefault(); close(); return; }
            else return;
            event.preventDefault(); optionRefs.current[next]?.focus();
          }} onClick={() => { onChange(field.field_code); close(); }} className={`flex w-full items-center gap-2 rounded-lg px-3 py-3 min-h-14 text-left hover:bg-green-50 focus:bg-green-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary ${field.field_code === fieldId ? "bg-green-50" : ""}`}>
          <CropIcon crop={field.crop_code} />
          <span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold text-foreground">{fieldDisplayName(field.field_code, field.field_id)}</span><span className="text-[11px] text-muted">{field.crop_code || "Crop unassigned"}</span></span>
          <SoilScore score={field.soil_health_score} />
          {field.field_code === fieldId && <Check aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-primary" />}
        </button>)}
        {!fields.length && <p className="p-3 text-sm text-muted">No fields available.</p>}
      </div>}
    </div>
  );
}
