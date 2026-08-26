import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import {
  clearToken,
  getCrawlJob,
  getStats,
  getToken,
  rebuildIndex,
  clearCache,
  startCrawl,
} from "../api/client";
import AdminLoginForm from "../components/AdminLoginForm";
import StatCard from "../components/StatCard";
import type { CrawlJob } from "../types/api";

export default function AdminPage() {
  const [loggedIn, setLoggedIn] = useState<boolean>(Boolean(getToken()));

  if (!loggedIn) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10">
        <AdminLoginForm onLoggedIn={() => setLoggedIn(true)} />
      </div>
    );
  }

  return <AdminDashboard onLogout={() => { clearToken(); setLoggedIn(false); }} />;
}

function AdminDashboard({ onLogout }: { onLogout: () => void }) {
  const queryClient = useQueryClient();
  const [seedUrl, setSeedUrl] = useState("");
  const [maxPages, setMaxPages] = useState(50);
  const [maxDepth, setMaxDepth] = useState(2);
  const [activeJob, setActiveJob] = useState<CrawlJob | null>(null);
  const [crawlError, setCrawlError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    refetchInterval: 15000,
  });

  const handleCrawlSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setCrawlError(null);
    setActionMessage(null);
    try {
      const job = await startCrawl(seedUrl, maxPages, maxDepth);
      setActiveJob(job);
      // Crawl runs synchronously server-side for the MVP; poll once more to
      // reflect the final persisted state, then refresh stats.
      const finalJob = await getCrawlJob(job.id);
      setActiveJob(finalJob);
      refetchStats();
    } catch (err) {
      setCrawlError(err instanceof Error ? err.message : "Crawl failed to start");
    }
  };

  const handleRebuild = async () => {
    setActionMessage(null);
    try {
      const result = await rebuildIndex();
      setActionMessage(`Index rebuilt: ${result.documents_indexed} documents indexed.`);
      refetchStats();
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : "Rebuild failed");
    }
  };

  const handleClearCache = async () => {
    setActionMessage(null);
    try {
      const result = await clearCache();
      setActionMessage(`Cache cleared: ${result.keys_cleared} keys removed.`);
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : "Cache clear failed");
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text">Admin Dashboard</h1>
        <button onClick={onLogout} className="text-sm text-muted hover:text-error transition-colors">
          Log out
        </button>
      </div>

      <section aria-labelledby="stats-heading" className="mb-8">
        <h2 id="stats-heading" className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Index Statistics
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Documents" value={stats?.document_count ?? "—"} />
          <StatCard label="Indexed Terms" value={stats?.indexed_terms ?? "—"} />
          <StatCard label="Crawled URLs" value={stats?.crawled_urls ?? "—"} />
          <StatCard label="Failed URLs" value={stats?.failed_urls ?? "—"} />
        </div>
      </section>

      <section aria-labelledby="crawl-heading" className="mb-8 rounded-lg border border-border bg-surface p-5">
        <h2 id="crawl-heading" className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted">
          Start a Crawl
        </h2>
        <form onSubmit={handleCrawlSubmit} className="grid gap-4 sm:grid-cols-[2fr_1fr_1fr_auto] sm:items-end">
          <div>
            <label htmlFor="seed-url" className="mb-1 block text-xs text-muted">
              Seed URL
            </label>
            <input
              id="seed-url"
              type="text"
              required
              placeholder="https://example.com"
              value={seedUrl}
              onChange={(e) => setSeedUrl(e.target.value)}
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </div>
          <div>
            <label htmlFor="max-pages" className="mb-1 block text-xs text-muted">
              Max pages
            </label>
            <input
              id="max-pages"
              type="number"
              min={1}
              max={500}
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </div>
          <div>
            <label htmlFor="max-depth" className="mb-1 block text-xs text-muted">
              Max depth
            </label>
            <input
              id="max-depth"
              type="number"
              min={0}
              max={5}
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary"
            />
          </div>
          <button
            type="submit"
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 transition-colors"
          >
            Start Crawl
          </button>
        </form>

        {crawlError && (
          <p role="alert" className="mt-3 text-sm text-error">
            {crawlError}
          </p>
        )}

        {activeJob && (
          <div className="mt-4 rounded border border-border bg-background p-3 font-mono text-xs text-muted">
            <p>Job: {activeJob.id}</p>
            <p>Status: {activeJob.status}</p>
            <p>
              Pages crawled: {activeJob.pages_crawled} · Failed: {activeJob.pages_failed}
            </p>
          </div>
        )}
      </section>

      <section aria-labelledby="maintenance-heading" className="rounded-lg border border-border bg-surface p-5">
        <h2 id="maintenance-heading" className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted">
          Maintenance
        </h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleRebuild}
            className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary transition-colors"
          >
            Rebuild Index
          </button>
          <button
            onClick={handleClearCache}
            className="rounded-lg border border-border px-4 py-2 text-sm hover:border-primary transition-colors"
          >
            Clear Cache
          </button>
        </div>
        {actionMessage && <p className="mt-3 text-sm text-muted">{actionMessage}</p>}
      </section>
    </div>
  );
}
