export interface SearchResultItem {
  id: string;
  title: string;
  url: string;
  snippet: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total: number;
  page: number;
  limit: number;
  latency_ms: number;
  cached: boolean;
  mode: "tfidf" | "bm25" | "hybrid";
}

export interface DocumentDetail {
  id: string;
  url: string;
  canonical_url: string;
  title: string | null;
  content: string;
  word_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface StatsResponse {
  document_count: number;
  indexed_terms: number;
  crawled_urls: number;
  failed_urls: number;
  last_indexing_time: string | null;
}

export interface CrawlJob {
  id: string;
  seed_url: string;
  max_pages: number;
  max_depth: number;
  status: "pending" | "running" | "completed" | "failed";
  pages_crawled: number;
  pages_failed: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface ApiError {
  error: string;
  detail?: unknown;
  status_code: number;
}
