export default function EmptyState() {
  return (
    <div role="status" className="rounded-lg border border-border bg-surface p-8 text-center">
      <p className="text-base font-medium text-text">No results found.</p>
      <p className="mt-2 text-sm text-muted">
        Try using fewer words, checking your spelling, or using broader keywords.
      </p>
    </div>
  );
}
