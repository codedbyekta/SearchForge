import { KeyboardEvent, useState } from "react";

interface SearchBarProps {
  initialQuery?: string;
  onSearch: (query: string) => void;
}

export default function SearchBar({ initialQuery = "", onSearch }: SearchBarProps) {
  const [value, setValue] = useState(initialQuery);

  const submit = () => {
    if (value.trim().length > 0) {
      onSearch(value.trim());
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") submit();
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-3 w-full rounded-xl border border-border bg-surface px-4 py-3 focus-within:border-primary transition-colors">
        <svg
          aria-hidden="true"
          className="h-5 w-5 text-muted shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11a6 6 0 11-12 0 6 6 0 0112 0z" />
        </svg>
        <input
          type="text"
          role="searchbox"
          aria-label="Search SearchForge"
          placeholder="Search indexed documents…"
          className="flex-1 bg-transparent outline-none text-base placeholder:text-muted"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={500}
        />
        {value.length > 0 && (
          <button
            type="button"
            aria-label="Clear search"
            className="text-muted hover:text-text transition-colors"
            onClick={() => setValue("")}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
        <button
          type="button"
          onClick={submit}
          className="rounded-lg bg-primary px-4 py-1.5 text-sm font-medium text-white hover:bg-primary/90 transition-colors"
        >
          Search
        </button>
      </div>
    </div>
  );
}
