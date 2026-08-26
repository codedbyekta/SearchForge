import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { search } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Pagination from "../components/Pagination";
import ResultCard from "../components/ResultCard";
import SearchBar from "../components/SearchBar";

const LIMIT = 10;

export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const page = Number(params.get("page") ?? "1");

  const [mode, setMode] = useState<"tfidf" | "bm25">("bm25");

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["search", query, page, mode],
    queryFn: () => search(query, page, LIMIT, mode),
    enabled: query.trim().length > 0,
    retry: false,
  });

  useEffect(() => {
    document.title = query ? `${query} — SearchForge` : "SearchForge";
  }, [query]);

  const handleSearch = (q: string) => {
    setParams({ q, page: "1" });
  };

  const handlePageChange = (newPage: number) => {
    setParams({ q: query, page: String(newPage) });
  };

  const totalPages = data ? Math.max(1, Math.ceil(data.total / LIMIT)) : 1;

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-text">SearchForge</h1>
        <p className="mt-1 text-sm text-muted">A hybrid keyword + ranking search engine, built from scratch.</p>
      </div>

      <SearchBar initialQuery={query} onSearch={handleSearch} />

      {query.trim().length > 0 && (
        <div className="mt-3 flex items-center justify-between text-xs text-muted">
          <div>
            {data && !isLoading && (
              <span>
                {data.total.toLocaleString()} result{data.total === 1 ? "" : "s"} · {data.latency_ms} ms
                {data.cached ? " · cached" : ""}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="mode-select" className="sr-only">
              Ranking mode
            </label>
            <select
              id="mode-select"
              value={mode}
              onChange={(e) => setMode(e.target.value as "tfidf" | "bm25")}
              className="rounded border border-border bg-surface px-2 py-1 font-mono text-xs text-muted"
            >
              <option value="bm25">BM25</option>
              <option value="tfidf">TF-IDF</option>
            </select>
          </div>
        </div>
      )}

      <div className="mt-6 space-y-3">
        {query.trim().length === 0 && (
          <p className="text-center text-sm text-muted">Enter a query above to search the index.</p>
        )}

        {isLoading && <LoadingState />}

        {isError && (
          <ErrorState
            onRetry={() => refetch()}
            message={error instanceof Error ? error.message : undefined}
          />
        )}

        {!isLoading && !isError && data && data.results.length === 0 && <EmptyState />}

        {!isLoading &&
          !isError &&
          data?.results.map((result) => <ResultCard key={result.id} result={result} />)}
      </div>

      {data && data.results.length > 0 && (
        <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
      )}
    </div>
  );
}
