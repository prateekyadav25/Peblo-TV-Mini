# Peblo TV Mini

A robust, full-stack catalogue publishing and streaming platform built for the Peblo TV Mini architecture challenge.

## 1. Project Overview

Peblo TV Mini is a content management and viewer platform. Editors can curate shows, seasons, episodes, and artwork. Admins publish the finalised content to a highly performant, read-optimised static catalogue consumed by the Viewer app.

## 2. Architecture Diagram

```text
[ CMS Frontend ] (React)
       | (CRUD & Auth)
       v
[ FastAPI Backend ] <---> [ PostgreSQL ]
       | (Admin Publish)
       v
[ Storage Backend ] (JSON Catalogue + Artwork)
       ^
       | (Read-Only)
[ Viewer Frontend ] (React)
```

## 3. Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (Async), PostgreSQL 16, Alembic
- **Frontend:** React 18, TypeScript, Vite, TanStack Query, TailwindCSS
- **Storage:** Local Disk (abstracted for cloud)

## 4. How to run with docker-compose

```bash
cp .env.example .env
docker-compose up -d --build
```

On startup, the system will automatically:

1. Wait for PostgreSQL to be healthy.
2. Run Alembic migrations.
3. Idempotently seed default admin/editor users.
4. Load `seed_shows.json` into draft shows, seasons, and episodes.

The repository currently contains no usable artwork files in `assets/`, so seeded content is deliberately draft content. Upload the required artwork in the CMS, then publish the show and episodes.

## 5. Default Development Users

- **Admin**: `admin_test@peblo.tv` (Password: `admin`)
- **Editor**: `editor_test@peblo.tv` (Password: `editor`)

## 6. Publishing Flow & Atomicity

For the local filesystem used by Compose, the application uses an **Atomic Write-then-Rename** strategy for generating the live catalogue:

1. **Generate**: The entire catalogue JSON is constructed in memory from a snapshot of the PostgreSQL database.
2. **Stage**: The JSON is written to a temporary staging key (`catalogue/staging-{uuid}.json`).
3. **Swap**: The staging file is atomically renamed to `catalogue/live.json` using `os.replace`.
4. **Record**: The run result is recorded in the `publish_runs` table.

**Why this matters**: Viewers always receive a fully valid JSON catalogue. If generation or staging fails, the existing live catalogue remains untouched. A crash after the file swap but before the database run update can leave the file ahead of run metadata; this is a known crash window.

## 7. Storage Abstraction

Artwork and the catalogue JSON are managed via a `StorageBackend` abstraction. The default `LocalStorageBackend` interacts with the local disk. It implements `rename()`, `put()`, `get()`, and `exists()`. Object storage has no filesystem rename, so production R2/S3 support requires immutable catalogue versions plus an atomic current-version pointer or provider conditional-write primitive.

## 8. Search Implementation

The search API (`GET /api/catalog/search`) fetches the live catalogue JSON into memory and applies deterministic normalization (case, whitespace) and compositional filtering (query, category, language, section). Query text matches show titles, episode titles, and categories.
**Scalability Limitation**: In-memory parsing works perfectly for thousands of records but will bottleneck RAM and CPU if the catalogue grows to hundreds of thousands of items. A scalable evolution would involve piping the JSON into an ElasticSearch index or an edge worker (like Cloudflare Workers KV).

## 9. Validation & RBAC

- **Validation**: Strict database constraints and API validations ensure integrity. The `DBValidator` ensures no show is published without artwork or valid sections.
- **RBAC**: `Depends(require_admin)` and `Depends(require_editor)` enforce permissions server-side. Editors can modify content, but only Admins can hit the publish endpoint.

## 10. Health Endpoints

- `/api/health`: Returns basic API status. Suitable for Docker container healthchecks and external pinging.

## 11. Workflow notes and limitations

- Episodes are created as drafts first. An editor uploads episode thumbnail artwork, then changes the episode status to published.
- Pagination is omitted from the Viewer API because it reads the entire static JSON catalogue in one chunk. CMS show listing is paginated server-side.
- Publish accepts an `Idempotency-Key` header. Retrying the same key returns the existing run instead of creating a duplicate publish.

## 12. Testing & CI

A pytest suite covers RBAC, content grouping, Season 0 handling, validation, search, CRUD, and publish behavior. CI runs PostgreSQL migration checks, backend tests, frontend builds, and ESLint. Run locally with `PYTHONPATH=backend pytest backend/tests -q`, `cd cms; npm run lint; npm run build`, and `cd viewer; npm run lint; npm run build`.

## 13. Decisions and Trade-offs

- **Postgres Advisory Locks vs Distributed Locks (Redis)**: The publish endpoint uses a PostgreSQL transaction advisory lock against Postgres. Trade-off: Avoids adding Redis but ties concurrency control to PostgreSQL.
- **In-Memory Catalogue Generation**: The JSON catalogue is built by pulling records into memory before writing to disk. Trade-off: Easy to implement and deterministic, but requires the worker to have enough RAM to hold the entire catalogue if it scales massively.
- **Nginx Static File Serving**: The Viewer app reads directly from Nginx static mounts (`/api/storage/`). Trade-off: Bypasses FastAPI completely for 100% read uptime and instant responses, but means the Viewer has zero server-side logic (e.g., personalized recommendations).
- **Search API Load**: The backend search loads the JSON on every request. Trade-off: Simplifies architecture (no Elasticsearch) but is CPU/Memory heavy for very large catalogues.
- **Stateless JWTs**: Used stateless JWTs for auth. Trade-off: Easy to scale and maintain, but tokens cannot be immediately revoked on the server.

## AI assistance

AI assistance was used to inspect the repository, identify contract mismatches, and draft implementation changes. The output was checked against the challenge brief, local tests, TypeScript builds, lint, and route/model relationships. Unsupported claims in the original README were removed rather than retained for presentation value.

## 14. Time Spent (Rough Estimates)

- **Phase 1-4 (Setup, Schema, CI)**: ~3 hours
- **Phase 5 (Auth & RBAC)**: ~2 hours
- **Phase 6 (CRUD APIs & Forms)**: ~3 hours
- **Phase 7 (Publishing Pipeline & Atomicity)**: ~4 hours
- **Phase 8 (Search & Viewer Isolation)**: ~3 hours
- **Phase 9 (Validation Report & Polish)**: ~2 hours
- **Total Time**: ~17 hours
