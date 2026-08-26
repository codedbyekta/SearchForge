# SearchForge

A from-scratch hybrid search engine: a crawler collects web documents, a
custom-built inverted index and BM25/TF-IDF ranking engine make them
searchable, and a FastAPI + React application exposes it all through a
developer-oriented search UI.

Built to the SearchForge PRD / SRS / System Architecture / UI-UX /
Development Plan documents — see [`docs/`](#project-documents) for the
original specs this implementation follows.

## What's implemented (MVP scope)

- **Crawler** — BFS crawl from a seed URL, robots.txt handling, retries with
  backoff, page/depth limits, per-job URL dedup, SSRF protection (blocks
  localhost, private IP ranges, cloud metadata endpoints).
- **Parser** — strips boilerplate (nav/footer/script/style), extracts title,
  headings, main text, and outbound links.
- **Text processing** — deterministic lowercasing, Unicode normalization,
  tokenization, stop-word removal, lightweight stemming.
- **Inverted index** — a real, from-scratch data structure (`term -> {doc_id:
  posting}`) with term frequency, positions, document-frequency lookups, and
  JSON persistence. Not delegated to Postgres full-text search.
- **Ranking** — both TF-IDF and BM25 (configurable `k1`/`b`), selectable per
  query.
- **Search API** — FastAPI, with query/pagination validation, structured
  errors, and search logging.
- **Caching** — Redis, with a hard requirement that Redis outages degrade to
  direct search rather than failing requests.
- **Auth** — JWT-based admin accounts; crawl/rebuild/cache-clear endpoints
  are admin-only, search/documents/stats are public.
- **React UI** — search page (loading/empty/error states, pagination, BM25 vs
  TF-IDF toggle), document detail page, and an admin dashboard (stats, crawl
  controls, index rebuild, cache clearing).
- **Tests** — 70 backend tests, 84% coverage (unit + integration, including
  SSRF/security cases).
- **Docker** — full `docker compose up` stack: frontend (nginx), backend
  (FastAPI/uvicorn), PostgreSQL, Redis.

**Deferred to post-MVP** (per the Development Plan, Phase 15 / P2):
embedding-based semantic retrieval and hybrid reranking. The `mode=bm25|tfidf`
query parameter and service layer are structured so a `semantic`/`hybrid`
mode can be added later without reworking the API contract.

## Architecture

```
                     ┌─────────────┐
   User Query ──────▶│   React UI   │
                     └──────┬──────┘
                            │ HTTP/JSON
                     ┌──────▼──────┐        ┌───────────┐
                     │  FastAPI    │◀──────▶│   Redis    │ (cache, fails open)
                     │  (API layer)│        └───────────┘
                     └──────┬──────┘
              ┌─────────────┼─────────────────┐
       ┌──────▼─────┐ ┌─────▼──────┐   ┌───────▼───────┐
       │  Inverted  │ │  BM25 /    │   │  PostgreSQL    │
       │  Index     │ │  TF-IDF    │   │  (metadata,    │
       │  (JSON,    │ │  Ranking   │   │   crawl jobs,  │
       │  in-proc)  │ │            │   │   users)       │
       └────────────┘ └────────────┘   └───────▲────────┘
                                                 │
       ┌───────────┐   ┌────────────┐   ┌───────┴───────┐
       │ Seed URL  │──▶│  Crawler   │──▶│ Parser +      │
       │ (admin)   │   │ (BFS, SSRF-│   │ Tokenizer +   │
       └───────────┘   │  safe)     │   │ Indexer       │
                        └────────────┘   └───────────────┘
```

Modular monolith, as specified in the System Architecture doc — no
microservices, no Kubernetes, no distributed crawling for the MVP. The crawl
endpoint runs synchronously within the request for this build; the service
layer (`crawl_service.start_crawl_job`) is isolated so it can be moved behind
a background worker/queue (Celery, RQ, arq) without touching the API or DB
layers, per the documented Stage 2/3 scalability plan.

## Project layout

```
searchforge/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI app, CORS, rate limiting, error handlers
│   │   ├── core/                config, security (JWT/bcrypt), SSRF validation, logging
│   │   ├── db/                  SQLAlchemy models, session, schema bootstrap
│   │   ├── schemas/              Pydantic request/response models
│   │   ├── search/               tokenizer, inverted index, TF-IDF, BM25
│   │   ├── crawler/              parser, URL manager, crawler engine
│   │   ├── services/              search/indexing/crawl/stats/auth orchestration
│   │   ├── api/v1/               search, documents, crawl, stats, admin, auth, health
│   │   └── cache/                 Redis wrapper (fail-open)
│   ├── scripts/create_admin.py    CLI to create an admin user
│   ├── tests/                     70 tests (unit + API integration)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                SearchPage, DocumentDetailPage, AdminPage
│   │   ├── components/            SearchBar, ResultCard, Pagination, Loading/Empty/ErrorState, ...
│   │   ├── api/client.ts          typed fetch wrapper
│   │   └── types/api.ts           shared response types
│   ├── nginx.conf                 SPA routing + /api reverse proxy
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Running locally with Docker (recommended)

```bash
cp backend/.env.example backend/.env   # edit JWT_SECRET_KEY at minimum
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

Create an admin user once the backend container is up:

```bash
docker compose exec backend python -m scripts.create_admin --username admin --password changeme
```

Log in at `/admin` in the UI with those credentials to start crawls, rebuild
the index, and clear the cache.

## Running locally without Docker

**Backend** (requires Python 3.12, PostgreSQL, Redis running locally):

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point DATABASE_URL / REDIS_URL at your local services
python -m app.db.init_db
python -m scripts.create_admin --username admin --password changeme
uvicorn app.main:app --reload
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/health` to `http://localhost:8000` in dev (see
`vite.config.ts`); override with `VITE_API_PROXY_TARGET` if needed.

## Running the test suite

```bash
cd backend
pip install -r requirements.txt
pytest -q --cov=app --cov-report=term-missing
```

70 tests / 84% coverage as of this build, covering: tokenizer determinism,
inverted index CRUD + persistence, TF-IDF/BM25 ranking correctness, URL
canonicalization, SSRF rejection (localhost, private ranges, cloud metadata,
`javascript:`/`file:` schemes), HTML parsing, indexing dedup-by-content-hash,
search-service validation/caching/pagination, crawl-job orchestration and
failure handling, JWT/password hashing, and API-level integration tests
(auth gating, 404/400/401/422 behavior, error responses that never leak
stack traces).

Frontend type-checking: `cd frontend && npx tsc -b`.

## API summary

| Method | Path                     | Auth       | Description                          |
|--------|--------------------------|------------|---------------------------------------|
| GET    | `/health`                | none       | Liveness check                        |
| GET    | `/api/v1/search`         | none       | `q`, `page`, `limit`, `mode=bm25|tfidf` |
| GET    | `/api/v1/documents/{id}` | none       | Document detail                       |
| GET    | `/api/v1/stats`          | none       | Index/crawl statistics                |
| POST   | `/api/v1/crawl`          | admin JWT  | Start a crawl job                     |
| GET    | `/api/v1/crawl/{id}`     | admin JWT  | Crawl job status                      |
| POST   | `/api/v1/admin/index/rebuild` | admin JWT | Rebuild the inverted index from stored documents |
| POST   | `/api/v1/admin/cache/clear`   | admin JWT | Clear cached search results |
| POST   | `/api/v1/auth/login`     | none       | Exchange credentials for a JWT        |

Full interactive docs at `/docs` (Swagger) once the backend is running.

## Security notes

- SSRF protection blocks `javascript:`/`file:` schemes, localhost/loopback,
  private/link-local/reserved IP ranges, and the `169.254.169.254` cloud
  metadata address — both for literal-IP URLs and DNS-resolved hostnames.
- Passwords are bcrypt-hashed; admin sessions use short-lived JWTs.
- All admin endpoints require a valid JWT with `role=admin`; regular users
  get 401/403, never a silent fallback.
- A simple in-memory rate limiter throttles per-IP request bursts; for a
  multi-instance deployment this should move to Redis (`INCR`+`EXPIRE`).
- Unhandled exceptions return a generic `{"error": "internal_error"}` body —
  stack traces are logged server-side only, never returned to the client.

## AWS deployment (per System Architecture 3.10)

The documented progression is: Docker on a single EC2 instance first, then
move to managed RDS PostgreSQL and ElastiCache Redis as the project grows.

1. **Single-instance MVP**: provision an EC2 instance, install Docker +
   Docker Compose, copy this repo, set real secrets in `backend/.env`
   (`JWT_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS` for your
   domain), and run `docker compose up -d --build`. Put a security group in
   front that only opens 80/443 (and 22 for your IP).
2. **Managed data services**: swap `DATABASE_URL` to an RDS PostgreSQL
   endpoint and `REDIS_URL` to an ElastiCache endpoint; drop the `postgres`
   and `redis` services from `docker-compose.yml` on the EC2 host.
3. **HTTPS**: terminate TLS with an ALB + ACM certificate in front of the
   EC2 instance (or Nginx + Let's Encrypt directly on the box for a simpler
   single-instance setup).
4. **Backups / logs / health checks**: enable RDS automated backups, ship
   container logs to CloudWatch Logs, and point an ALB health check (or
   Route 53 health check) at `/health`.
5. **Scaling beyond MVP** (System Architecture 3.12): put the API behind a
   load balancer with multiple instances (Stage 2), then move crawling to a
   dedicated worker behind a queue (Stage 3) before considering sharded
   indexes or distributed crawling.

This build does not include Terraform/CDK or an actual live AWS deployment —
it's structured so that progression is a configuration change, not a
rewrite.

## Project documents

This implementation follows five source documents supplied for the project:
Product Requirements (PRD), Software Requirements Specification (SRS),
System Architecture, UI/UX Design, and Development Plan. Notable decisions
made where the docs left room for judgment:

- BM25 is the default ranking mode (PRD: "preferably BM25"); TF-IDF remains
  available via `mode=tfidf` for comparison.
- The inverted index persists to JSON on disk (System Architecture 3.8
  explicitly allows "serialized files" for the MVP) rather than a custom
  binary format.
- The crawl endpoint runs synchronously in-request for this build rather
  than via a background worker, since the Development Plan's Phase 0
  "background workers" note is aspirational architecture, not an MVP
  requirement — see the Architecture section above for how it's isolated to
  make that swap straightforward later.
