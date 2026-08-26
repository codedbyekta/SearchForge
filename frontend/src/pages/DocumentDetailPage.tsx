import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getDocument } from "../api/client";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["document", id],
    queryFn: () => getDocument(id as string),
    enabled: Boolean(id),
    retry: false,
  });

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link to="/" className="text-sm text-muted hover:text-primary transition-colors">
        &larr; Back to search
      </Link>

      <div className="mt-6">
        {isLoading && <LoadingState />}
        {isError && <ErrorState onRetry={() => refetch()} />}

        {data && (
          <article>
            <h1 className="text-2xl font-bold text-text">{data.title || data.url}</h1>
            <p className="mt-1 font-mono text-sm text-success break-all">{data.url}</p>
            <div className="mt-3 flex flex-wrap gap-4 font-mono text-xs text-muted">
              <span>{data.word_count.toLocaleString()} words</span>
              <span>Status: {data.status}</span>
              <span>Updated: {new Date(data.updated_at).toLocaleString()}</span>
            </div>
            <div className="mt-6 rounded-lg border border-border bg-surface p-5 leading-relaxed text-sm text-text whitespace-pre-wrap">
              {data.content}
            </div>
          </article>
        )}
      </div>
    </div>
  );
}
