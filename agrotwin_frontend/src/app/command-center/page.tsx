"use client";

import React from "react";
import Link from "next/link";
import { getFields, getTwin, fieldDisplayName, ApiError, type FieldSummary, type TwinResponse } from "@/lib/api";
import { RefreshCw, ShieldAlert } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

type FleetRow = {
  field: FieldSummary;
  twin: TwinResponse | null;
  twinError: string | null;
};

function confidenceBadgeClass(confidence: string | undefined): string {
  const level = (confidence || "").toUpperCase();
  if (level === "HIGH") return "bg-green-50 text-green-700 border-green-200";
  if (level === "MEDIUM") return "bg-accent-bg text-accent border-accent/30";
  if (level === "LOW") return "bg-orange-50 text-orange-700 border-orange-200";
  if (level === "ABSTAIN") return "bg-red-50 text-red-700 border-red-200";
  return "bg-surface-hover text-muted border-border";
}

function StatusLabel({ row }: { row: FleetRow }) {
  const { t } = useLanguage();
  if (row.twinError) return <span className="bg-red-50 text-red-700 border-red-200">{t("cc.unreachable")}</span>;
  if (!row.twin) return <span className="bg-surface-hover text-muted border-border">{t("cc.loading")}</span>;
  if (!row.twin.hasSoilTest) return <span className="bg-surface-hover text-muted border-border">{t("cc.noSoil")}</span>;
  const status = row.twin.currentPlan?.status;
  if (status === "ABSTAIN") return <span className="bg-red-50 text-red-700 border-red-200">{t("cc.abstained")}</span>;
  if (status === "NO_DATA") return <span className="bg-accent-bg text-accent border-accent/30">{t("cc.noPlan")}</span>;
  return <span className="bg-green-50 text-green-700 border-green-200">{t("cc.planActive")}</span>;
}

export default function CommandCenterPage() {
  const { t } = useLanguage();
  const [rows, setRows] = React.useState<FleetRow[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const fetchFleet = React.useCallback(() => {
    setLoading(true);
    getFields()
      .then(async (fields) => {
        setError(null);
        // Seed rows immediately so the table renders while per-field twins load.
        setRows(fields.map((field) => ({ field, twin: null, twinError: null })));
        const results = await Promise.all(
          fields.map((field) =>
            getTwin(field.field_code)
              .then((twin): FleetRow => ({ field, twin, twinError: null }))
              .catch((err): FleetRow => ({
                field,
                twin: null,
                twinError: err instanceof ApiError ? err.message : "Unreachable",
              }))
          )
        );
        setRows(results);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not reach the Kisan Saathi backend.");
        setLoading(false);
      });
  }, []);

  // Intentional: fetch on mount, not derived from render.
  /* eslint-disable react-hooks/set-state-in-effect */
  React.useEffect(() => {
    fetchFleet();
  }, [fetchFleet]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const total = rows?.length ?? 0;
  const needsAttention = (rows || []).filter((r) => r.twin?.currentPlan?.status === "ABSTAIN" || r.twinError).length;
  const activeAlerts = (rows || []).filter((r) => r.twin?.activeAlert != null).length;

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-border bg-surface">
        <div className="container mx-auto px-4 py-6">
          <p className="text-xs font-bold uppercase tracking-widest text-primary mb-1">Command Center</p>
          <h1 className="font-serif text-2xl font-bold text-foreground">Fleet overview — all registered fields</h1>
          <p className="text-sm text-muted mt-1 max-w-2xl">
            Each row reads the same live <code className="text-[11px]">/twin</code> state the field&apos;s own
            dashboard shows — this is a summary view, not a separate data source.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Summary strip */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
          <div className="bg-surface border border-border gov-panel p-4">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-muted mb-1">Total fields</div>
            <div className="text-3xl font-extrabold font-serif text-foreground">{total || "—"}</div>
          </div>
          <div className="bg-surface border border-border gov-panel p-4">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-muted mb-1">Needs attention</div>
            <div className={`text-3xl font-extrabold font-serif ${needsAttention > 0 ? "text-red-600" : "text-foreground"}`}>{needsAttention}</div>
          </div>
          <div className="bg-surface border border-border gov-panel p-4">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-muted mb-1">Active alerts</div>
            <div className={`text-3xl font-extrabold font-serif ${activeAlerts > 0 ? "text-accent" : "text-foreground"}`}>{activeAlerts}</div>
          </div>
        </div>

        <div className="flex items-center justify-end mb-3">
          <button onClick={fetchFleet} disabled={loading} className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-primary transition disabled:opacity-50">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> {t("cc.refresh")}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-4 gov-panel mb-4">
            {error} <button onClick={fetchFleet} className="underline font-semibold ml-1">{t("ins.retry")}</button>
          </div>
        )}

        {rows === null && !error && (
          <div className="text-sm text-muted py-10 text-center">{t("cc.loading")}</div>
        )}

        {rows !== null && rows.length === 0 && (
          <div className="bg-surface border border-border gov-panel p-10 text-center text-sm text-muted">
            {t("cc.noFields")}
          </div>
        )}

        {rows !== null && rows.length > 0 && (
          <div className="bg-surface border border-border gov-panel overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-[11px] font-semibold uppercase tracking-wide text-muted">
                  <th className="px-4 py-3">Field</th>
                  <th className="px-4 py-3">Crop / Stage</th>
                  <th className="px-4 py-3">Soil Health</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3">Alert</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  return (
                    <tr key={row.field.field_code} className="border-b border-border last:border-0 hover:bg-surface-hover">
                      <td className="px-4 py-3 font-semibold text-foreground">{fieldDisplayName(row.field.field_code, row.field.field_id)}</td>
                      <td className="px-4 py-3 text-muted">
                        {row.twin ? `${row.twin.crop || "—"} · ${row.twin.growthStage || "—"}` : (row.field.crop_code || "—")}
                      </td>
                      <td className="px-4 py-3">
                        {row.twin?.soilHealthScore != null ? (
                          <span className="font-semibold text-foreground">{row.twin.soilHealthScore}/100</span>
                        ) : (
                          <span className="text-muted">Not available</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <StatusLabel row={row} />
                      </td>
                      <td className="px-4 py-3">
                        {row.twin?.currentPlan?.confidence ? (
                          <span className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full border ${confidenceBadgeClass(row.twin.currentPlan.confidence)}`}>
                            {row.twin.currentPlan.confidence}
                          </span>
                        ) : (
                          <span className="text-muted text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {row.twin?.activeAlert ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-accent">
                            <ShieldAlert className="w-3.5 h-3.5" /> {row.twin.activeAlert.title}
                          </span>
                        ) : (
                          <span className="text-muted text-xs">None</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link href={`/dashboard?field=${encodeURIComponent(row.field.field_code)}`} className="text-xs font-semibold text-primary hover:underline">
                          Open →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
