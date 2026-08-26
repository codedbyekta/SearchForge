interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <nav aria-label="Search results pagination" className="flex items-center justify-center gap-4 py-6">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="rounded-lg border border-border px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:border-primary transition-colors"
      >
        Previous
      </button>
      <span className="font-mono text-sm text-muted">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="rounded-lg border border-border px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:border-primary transition-colors"
      >
        Next
      </button>
    </nav>
  );
}
