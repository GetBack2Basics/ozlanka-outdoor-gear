"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";

type ScrapeRun = {
  id: number;
  status: string;
  stage: string;
  progress_percent: number;
  message: string | null;
  total_items: number;
  processed_items: number;
  started_at: string;
  finished_at: string | null;
};

export function ScrapePanel({ initialRun }: { initialRun: ScrapeRun | null }) {
  const [run, setRun] = useState<ScrapeRun | null>(initialRun);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const active = useMemo(() => run?.status === "queued" || run?.status === "running", [run]);

  useEffect(() => {
    if (!run || !active) return;
    const timer = window.setInterval(async () => {
      const response = await fetch("/api/admin/scrape/latest", { cache: "no-store" });
      if (!response.ok) return;
      const payload = await response.json();
      if (payload.run) {
        setRun(payload.run);
      }
    }, 2500);

    return () => window.clearInterval(timer);
  }, [run, active]);

  async function triggerScrape() {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/admin/scrape", { method: "POST" });
      if (!response.ok) {
        throw new Error("Failed to queue scrape");
      }
      const payload = await response.json();
      setRun(payload.run);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  const statusLabel = run
    ? `${run.status} · ${run.stage} · ${run.progress_percent}%`
    : "No scrape run yet";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Scrape status</h2>
          <p className="text-sm text-slate-600">{statusLabel}</p>
          {run?.message ? <p className="text-sm text-slate-500">{run.message}</p> : null}
        </div>
        <Button type="button" onClick={triggerScrape} disabled={busy}>
          {busy ? "Queuing..." : "Trigger Scrape Now"}
        </Button>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-slate-900 transition-all"
          style={{ width: `${run?.progress_percent ?? 0}%` }}
        />
      </div>

      <div className="mt-3 text-sm text-slate-600">
        {run ? (
          <>
            Processed {run.processed_items} / {run.total_items} source URLs
          </>
        ) : (
          "No scrape has been triggered yet."
        )}
      </div>

      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
