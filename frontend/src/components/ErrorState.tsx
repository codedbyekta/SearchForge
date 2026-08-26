interface ErrorStateProps {
  onRetry: () => void;
  message?: string;
}

export default function ErrorState({ onRetry, message }: ErrorStateProps) {
  return (
    <div role="alert" className="rounded-lg border border-error/40 bg-error/10 p-8 text-center">
      <p className="text-base font-medium text-text">Something went wrong.</p>
      {message && <p className="mt-1 text-sm text-muted">{message}</p>}
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 transition-colors"
      >
        Try Again
      </button>
    </div>
  );
}
