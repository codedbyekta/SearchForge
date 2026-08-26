import { Link } from "react-router-dom";
import type { SearchResultItem } from "../types/api";

interface ResultCardProps {
  result: SearchResultItem;
}

export default function ResultCard({ result }: ResultCardProps) {
  return (
    <article className="rounded-lg border border-border bg-surface p-4 hover:border-primary/50 transition-colors">
      <Link to={`/document/${result.id}`} className="block group">
        <h3 className="text-lg font-semibold text-text group-hover:text-primary transition-colors">
          {result.title}
        </h3>
        <p className="mt-1 truncate font-mono text-xs text-success">{result.url}</p>
        <p className="mt-2 text-sm text-muted leading-relaxed">{result.snippet}</p>
        <p className="mt-2 font-mono text-xs text-muted">Score: {result.score.toFixed(2)}</p>
      </Link>
    </article>
  );
}
