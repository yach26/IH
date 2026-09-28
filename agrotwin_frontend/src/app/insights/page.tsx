"use client";

import React from "react";
import Link from "next/link";
import { getAllAlerts, ApiError, type Alert } from "@/lib/api";
import { Bell, RefreshCw } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

function severityBadgeClass(severity: string | null): string {
  const level = (severity || "").toUpperCase();
  if (level === "HIGH" || level === "CRITICAL") return "bg-red-50 text-red-700 border-red-200";
  if (level === "MEDIUM") return "bg-accent-bg text-accent border-accent/30";
  if (level === "LOW") return "bg-green-50 text-green-700 border-green-200";
  return "bg-surface-hover text-muted border-border";
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const diffMs = Date.now() - then;
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  const days = Math.round(hrs / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

const SEVERITY_FILTERS = ["ALL", "HIGH", "MEDIUM", "LOW"] as const;

export default function InsightsPage() {
  const { t } = useLanguage();
  const [alerts, setAlerts] = React.useState<Alert[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [filter, setFilter] = React.useState<(typeof SEVERITY_FILTERS)[number]>("ALL");

  const fetchAlerts = React.useCallback(() => {
    getAllAlerts(100)
      .then((data) => {
        setAlerts(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not reach the Kisan Saathi backend."));
  }, []);

  React.useEffect(() => {
    fetchAlerts();
    // Same "no one has to ask" pattern as the dashboard — a heavy-rain replan
    // on any field should surface here without a manual refresh.
    const id = setInterval(fetchAlerts, 20000);
    return () => clearInterval(id);
  }, [fetchAlerts]);

  const filtered = (alerts || []).filter(
    (a) => filter === "ALL" || (a.severity || "").toUpperCase() === filter
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-border bg-surface">
        <div className="container mx-auto px-4 py-6">
          <p className="text-xs font-bold uppercase tracking-widest text-primary mb-1">{t("ins.badge")}</p>
          <h1 className="font-serif text-2xl font-bold text-foreground">{t("ins.title")}</h1>
          <p className="text-sm text-muted mt-1 max-w-2xl">
            Every entry here comes from a real event on the event bus (replans triggered by weather,
            soil-data changes, or validation conflicts) — nothing on this page is invented.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <div className="flex items-center gap-1.5">
            {SEVERITY_FILTERS.map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`text-xs font-semibold px-3 py-1.5 gov-panel border transition ${
                  filter === s ? "bg-primary text-white border-primary" : "bg-surface text-muted border-border hover:border-primary/40"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
          <button onClick={fetchAlerts} className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted hover:text-primary transition">
            <RefreshCw className="w-3.5 h-3.5" /> {t("ins.refresh")}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-4 gov-panel mb-4">
            {error} <button onClick={fetchAlerts} className="underline font-semibold ml-1">{t("ins.retry")}</button>
          </div>
        )}

        {alerts === null && !error && (
          <div className="text-sm text-muted py-10 text-center">{t("ins.loading")}</div>
        )}

        {alerts !== null && filtered.length === 0 && (
          <div className="bg-surface border border-border gov-panel p-10 text-center text-sm text-muted">
            {filter !== "ALL" ? filter.toLowerCase() + "-severity alerts" : t("ins.empty")}
          </div>
        )}

        <div className="space-y-2">
          {filtered.map((a) => (
            <div key={a.alert_id} className="bg-surface border border-border gov-panel p-4 flex items-start gap-3">
              <span className={`flex-shrink-0 mt-0.5 border rounded-full p-1.5 ${severityBadgeClass(a.severity)}`}>
                <Bell className="w-3.5 h-3.5" />
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full border ${severityBadgeClass(a.severity)}`}>
                    {a.severity || "INFO"}
                  </span>
                  <span className="text-xs font-semibold text-foreground">{a.alert_type.replace(/_/g, " ")}</span>
                  {a.field_code && (
                    <Link href={`/dashboard?field=${encodeURIComponent(a.field_code)}`} className="text-xs font-semibold text-primary hover:underline">
                      {a.field_code}
                    </Link>
                  )}
                  {a.resolved_at && (
                    <span className="text-[10px] text-green-700 bg-green-50 border border-green-200 rounded-full px-2 py-0.5">{t("ins.resolved")}</span>
                  )}
                </div>
                <p className="text-sm text-muted leading-relaxed">{a.message || t("ins.noDetail")}</p>
                <p className="text-[11px] text-muted/70 mt-1">{timeAgo(a.triggered_at)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
