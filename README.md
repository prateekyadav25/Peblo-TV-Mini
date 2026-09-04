# Peblo TV Mini

A robust, full-stack catalogue publishing and streaming platform built for the Peblo TV Mini architecture challenge.

This document provides a comprehensive overview of the system architecture, data flow, pipeline mechanisms, design choices, and how to run the project.

---

## 1. High-Level Architecture Overview

Peblo TV Mini is divided into three distinct operational layers, unified by a robust backend and an atomic publishing pipeline.

```text
+---------------------+
|   CMS Frontend      |
| (React, TypeScript) |
+---------+-----------+
          | (CRUD, Uploads, Publish Trigger)
          v
+---------+-----------+       +-------------------+
|   FastAPI Backend   | <---> | PostgreSQL (16)   |
| (Python 3.12, Auth) |       | (Relational Data) |
+---------+-----------+       +-------------------+
          | (Generates Catalogue JSON & Handles Storage)
          v
+---------+-----------+
|   Storage Backend   |
| (Local/Cloud Disk)  |
+---------+-----------+
          ^
          | (Reads Static JSON Catalogue & Assets)
          |
+---------+-----------+
|   Viewer Frontend   |
| (React, TypeScript) |
+---------------------+
```

### Flow Summary
1. **CMS Input**: Content Editors use the CMS to create Draft Shows, Seasons, and Episodes, and upload Artwork (in 3 defined dimensions).
2. **Validation**: The backend continuously validates the integrity of the drafts (e.g. valid sections, presence of required artwork).
3. **Publishing**: Admins hit the `Publish` endpoint. The backend pulls data from PostgreSQL, builds an optimized JSON catalogue, and atomically swaps it onto the storage layer.
4. **Consumption**: The Viewer application entirely bypasses the API database for content reads, instead fetching the static JSON catalogue directly. This isolates Viewer traffic from the CMS/API infrastructure.

---

## 2. Tech Stack Breakdown

- **Backend / API Core**: Python 3.12, FastAPI, SQLAlchemy (Async), PostgreSQL 16, Alembic (Migrations)
- **Frontend (CMS & Viewer)**: React 18, TypeScript, Vite, TanStack Query, TailwindCSS, React Router
- **Storage / Infrastructure**: Local Disk via a Swappable Abstraction Layer (Dockerized Nginx serves static files for the Viewer).
- **Authentication**: Stateless JWT Authentication.

---

## 3. Data Model & Relationships

The relational schema is built to represent the hierarchical nature of TV content while enforcing strict constraints:

- **Shows**: The top-level entity. Must have a valid `section` (e.g., Kids, Action) and associated poster/banner artwork.
- **Seasons**: Children of Shows. Note: **Season 0** is strictly reserved for trailers and handled specially in the viewer.
- **Episodes**: Children of Seasons.
- **Content Groups (Languages)**: Episodes that represent the same content but in different languages share a `content_group` ID. During publishing, the backend collapses these variants into a single catalogue entry with a `languages` list (e.g., `['en', 'hi']`).
- **Artwork**: Managed Polymorphically or via strict Foreign Keys. Uploads enforce strict dimensions and aspect ratios (Poster 2:3, Banner 16:9, Thumbnail 16:9) and a 200KB file limit.

---

## 4. The Atomic Publishing Pipeline

The crux of the system is how data moves from draft state in Postgres to live state in the Viewer. We use an **Atomic Write-then-Rename** strategy.

### Publishing Steps:
1. **Concurrency Lock**: The API acquires a PostgreSQL Transaction Advisory Lock. This ensures no two publish jobs can run concurrently in a multi-instance setup.
2. **Generate**: The entire catalogue JSON is constructed in memory from a DB snapshot. Invalid drafts are ignored. Grouping logic (collapsing language variants via `content_group`) is applied.
3. **Stage**: The JSON is written to a temporary staging file: `catalogue/staging-{uuid}.json`.
4. **Swap (Atomic)**: The staging file is atomically renamed to `catalogue/live.json` using `os.replace`.
5. **Record**: The outcome, timestamp, and metrics are recorded in the `publish_runs` database table.

**Why Atomic?** Viewers reading the catalogue must never encounter a half-written file. If the process crashes mid-generation, the old catalogue remains safely in place.

---

## 5. Storage Abstraction

Artwork and the catalogue JSON are managed via a `StorageBackend` interface.
- **Current**: `LocalStorageBackend` interacts with the local disk. It implements `rename()`, `put()`, `get()`, and `exists()`.
- **Extensibility**: To migrate to Cloudflare R2 or AWS S3, a developer only needs to write an `S3StorageBackend` class. *Note: Object stores lack a true atomic directory rename. For S3, we would generate a versioned catalogue (`catalogue-v2.json`) and update a pointer/symlink or use a provider conditional-write primitive.*

---

## 6. Search Implementation

The search API (`GET /api/catalog/search`) works directly off the static catalogue.
- It fetches the live catalogue JSON into memory and applies deterministic normalization (case, whitespace) and compositional filtering (query, category, language, section).
- Query text matches Show Titles, Episode Titles, and Categories.
- **Scalability Note**: In-memory parsing is blazing fast for small/medium catalogues (thousands of items). For catalogues scaling to hundreds of thousands of items, this design gracefully allows piping the JSON into ElasticSearch or utilizing Edge computing (e.g., Cloudflare Workers KV) without altering the Postgres DB.

---

## 7. Role-Based Access Control (RBAC) & Validation

- **RBAC**: enforced rigorously at the API layer.
  - **Editor**: Can perform CRUD operations and upload assets.
  - **Admin**: Can perform Editor actions *plus* trigger the Publish job.
- **Validation Report**: The CMS includes a Validation Report view that aggregates all blockers (missing artwork, invalid states) preventing a publish. This enables Editors to self-serve fixes without engineering support.

---

## 8. Setup & Running Locally

The entire stack is containerized for zero-friction setup.

### Prerequisites
- Docker & Docker Compose

### Commands
```bash
cp .env.example .env
docker-compose up -d --build
```

### On Startup, the system automatically:
1. Waits for PostgreSQL to become healthy.
2. Runs Alembic database migrations.
3. Idempotently seeds default Users (Admin/Editor).
4. Loads `seed_shows.json` into draft models.
*Note: Seeded content lacks artwork initially. Upload artwork in the CMS to clear validation blockers and publish.*

---

## 9. Default Users

- **Admin**: `admin_test@peblo.tv` / Password: `admin`
- **Editor**: `editor_test@peblo.tv` / Password: `editor`

---

## 10. Design Decisions and Trade-offs

1. **Postgres Advisory Locks vs Redis**: Used Postgres locks for publish concurrency. *Trade-off:* Eliminates Redis dependency, simplifying deployment, but ties lock scaling to the Postgres instance.
2. **In-Memory Catalogue Generation**: *Trade-off:* Deterministic and simple, but requires backend workers to have sufficient RAM as the catalogue grows exponentially.
3. **Viewer Reads from Nginx**: The Viewer app bypasses FastAPI completely to read the static JSON via Nginx. *Trade-off:* 100% read uptime and massive throughput scalability. However, the Viewer lacks server-side personalization (recommendations must be handled client-side or via a separate microservice).
4. **Stateless JWTs**: *Trade-off:* Highly scalable and stateless, but tokens cannot be immediately revoked server-side without a blacklist layer.

---

## 11. Testing & CI/CD

- **Tests**: A robust Pytest suite covers RBAC, content grouping, Season 0 trailer logic, API validation, search edge cases, and the publish atomic swap.
- **CI/CD**: Prepared for GitHub Actions. Runs PostgreSQL migration checks, backend tests, frontend Vite builds, and ESLint.

---

## 12. Time Spent (Estimates)

- Phase 1-4 (Setup, Schema, CI): ~3 hours
- Phase 5 (Auth & RBAC): ~2 hours
- Phase 6 (CRUD APIs & Forms): ~3 hours
- Phase 7 (Publishing Pipeline & Atomicity): ~4 hours
- Phase 8 (Search & Viewer Isolation): ~3 hours
- Phase 9 (Validation Report & Polish): ~2 hours
- **Total Time**: ~17 hours

---
*Peblo TV Mini Challenge Implementation*
