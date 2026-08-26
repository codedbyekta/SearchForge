export default function LoadingState() {
  return (
    <div aria-busy="true" aria-label="Loading results" className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="rounded-lg border border-border bg-surface p-4 animate-pulse">
          <div className="h-4 w-2/5 rounded bg-border" />
          <div className="mt-2 h-3 w-1/4 rounded bg-border" />
          <div className="mt-3 h-3 w-full rounded bg-border" />
          <div className="mt-1 h-3 w-4/5 rounded bg-border" />
        </div>
      ))}
    </div>
  );
}
