"""
Catalogue Publishing Service
=============================

ATOMICITY MECHANISM
-------------------
The catalogue is published using a write-then-rename strategy:

1. GENERATE: The entire catalogue JSON is built in-memory from a single
   database snapshot (one SELECT query per entity type, all within the
   same transaction isolation level).

2. STAGE: The JSON is written to a STAGING key in storage:
   "catalogue/staging-{run_id}.json"
   At this point, readers still see the previous live catalogue.

3. SWAP: The staging key is atomically renamed to the LIVE key:
   "catalogue/live.json"
   On local filesystems, os.replace() is atomic within the same
   filesystem. On cloud storage (S3/R2), this would be a copy+delete.

4. RECORD: The publish_run row is updated to mark success and
   is_current=True. Previous runs are marked is_current=False.

FAILURE MODES
-------------
- If generation fails: No staging file is written. The live catalogue
  is untouched. The publish_run records the error.

- If staging write fails: Same as above. No rename happens.

- If rename fails: The staging file exists but is never promoted. The
  live catalogue is the previous valid version. The publish_run
  records the error. A subsequent publish will overwrite the orphaned
  staging file.

- If the database update fails after rename: The file is already live
  (correct). The publish_run may show "failed" but the catalogue is
  consistent. A subsequent publish will correct the metadata.

CONCURRENCY
-----------
A simple in-process asyncio.Lock prevents two concurrent publish
operations from interleaving. In a multi-process deployment, this
would be replaced by a PostgreSQL advisory lock or a database-level
SELECT ... FOR UPDATE on a singleton publish_lock row.

IDEMPOTENCY
-----------
Repeated publishes with unchanged data produce byte-identical JSON
because:
- All queries use deterministic ORDER BY clauses
- UUIDs from the database are stable
- JSON keys are sorted via sort_keys=True
- Timestamps are not embedded (only data-derived fields)
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.artwork import Artwork
from app.models.episode import Episode
from app.models.publish_run import PublishRun
from app.models.season import Season
from app.models.show import Show
from app.storage.base import StorageBackend

logger = logging.getLogger(__name__)

LIVE_CATALOGUE_KEY = "catalogue/live.json"


def _staging_key(run_id: uuid.UUID) -> str:
    return f"catalogue/staging-{run_id}.json"


class CatalogueService:
    """Builds, stages, and atomically publishes the catalogue JSON."""

    @staticmethod
    async def publish(
        db: AsyncSession,
        storage: StorageBackend,
        triggered_by_user_id: uuid.UUID,
        idempotency_key: Optional[str] = None,
    ) -> PublishRun:
        """
        Execute a full catalogue publish. Returns the PublishRun record.

        This method is the ONLY entry point for publishing. It:
        1. Acquires a postgres advisory lock to prevent concurrent runs across workers.
        2. Creates a PublishRun with status='running'
        3. Generates the catalogue JSON
        4. Writes it to a staging key
        5. Atomically renames staging -> live
        6. Updates the PublishRun to status='success'
        """
        # 1. Acquire DB advisory lock (12345 is our publish lock ID)
        # Using xact_lock means it releases automatically at transaction end (commit/rollback)
        if db.bind and db.bind.dialect.name == 'postgresql':
            result = await db.execute(text("SELECT pg_try_advisory_xact_lock(12345)"))
            locked = result.scalar()
            if not locked:
                raise HTTPException(
                    status_code=409,
                    detail="A publish operation is already in progress."
                )

        if idempotency_key:
            result = await db.execute(
                select(PublishRun).where(PublishRun.idempotency_key == idempotency_key)
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                if existing.status == "running":
                    raise HTTPException(status_code=409, detail="This publish request is already running.")
                return existing

        # Enforce that publish decision and validation report agree
        from app.services.validation_service import DBValidator
        report = await DBValidator.generate_report(db)
        if report["total_errors"] > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot publish: there are blocking validation errors in the catalogue."
            )
        
        return await CatalogueService._do_publish(
            db, storage, triggered_by_user_id, idempotency_key
        )

    @staticmethod
    async def _do_publish(
        db: AsyncSession,
        storage: StorageBackend,
        triggered_by_user_id: uuid.UUID,
        idempotency_key: Optional[str] = None,
    ) -> PublishRun:
        # --- Step 1: Create the PublishRun record ---
        run = PublishRun(
            triggered_by=triggered_by_user_id,
            status="running",
            started_at=datetime.now(timezone.utc),
            shows_count=0,
            episodes_count=0,
            idempotency_key=idempotency_key,
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_id = run.id

        try:
            # --- Step 2: Build catalogue from DB snapshot ---
            catalogue, stats = await CatalogueService._build_catalogue(db)

            # --- Step 3: Serialize to deterministic JSON ---
            catalogue_bytes = json.dumps(
                catalogue, sort_keys=True, ensure_ascii=False, indent=2
            ).encode("utf-8")

            # --- Step 4: Write to staging key ---
            staging = _staging_key(run_id)
            await storage.put(staging, catalogue_bytes, "application/json")

            # --- Step 5: Atomic rename staging -> live ---
            await storage.publish_atomic(staging, LIVE_CATALOGUE_KEY)

            # --- Step 6: Update PublishRun to success ---
            # First, clear any previous is_current flags
            await db.execute(
                update(PublishRun)
                .where(PublishRun.is_current == True)
                .values(is_current=False)
            )
            run.status = "success"
            run.completed_at = datetime.now(timezone.utc)
            run.shows_count = stats["shows"]
            run.episodes_count = stats["episodes"]
            run.catalogue_key = LIVE_CATALOGUE_KEY
            run.is_current = True
            await db.commit()

            logger.info(
                "Catalogue published successfully: run=%s shows=%d episodes=%d",
                run_id, stats["shows"], stats["episodes"],
            )
            return run

        except Exception as exc:
            # --- Failure path: record the error ---
            logger.error("Catalogue publish failed: run=%s error=%s", run_id, exc)
            try:
                await db.rollback()
                # Re-fetch the run in a clean state
                result = await db.execute(
                    select(PublishRun).where(PublishRun.id == run_id)
                )
                run = result.scalar_one()
                run.status = "failed"
                run.completed_at = datetime.now(timezone.utc)
                run.error_message = str(exc)[:2000]
                await db.commit()
            except Exception as inner_exc:
                logger.error(
                    "Failed to record publish failure: %s", inner_exc
                )
            raise

    @staticmethod
    async def _build_catalogue(
        db: AsyncSession,
    ) -> tuple[dict[str, Any], dict[str, int]]:
        """
        Query the database for all published content and build the
        catalogue structure.

        Returns (catalogue_dict, stats_dict).
        """
        # --- Fetch all published shows ---
        result = await db.execute(
            select(Show)
            .where(Show.status == "published")
            .order_by(Show.section, Show.slug)
        )
        shows = result.scalars().all()

        # --- Fetch all seasons for those shows (exclude nothing yet) ---
        show_ids = [s.id for s in shows]
        if not show_ids:
            return {"sections": {}}, {"shows": 0, "episodes": 0}

        result = await db.execute(
            select(Season)
            .where(Season.show_id.in_(show_ids))
            .order_by(Season.show_id, Season.season_number)
        )
        all_seasons = result.scalars().all()

        # --- Fetch all published episodes ---
        season_ids = [s.id for s in all_seasons]
        if not season_ids:
            episodes = []
        else:
            result = await db.execute(
                select(Episode)
                .where(
                    Episode.season_id.in_(season_ids),
                    Episode.status == "published",
                )
                .order_by(
                    Episode.season_id,
                    Episode.episode_number,
                    Episode.language,
                )
            )
            episodes = result.scalars().all()

        # --- Fetch show artworks ---
        result = await db.execute(
            select(Artwork)
            .where(Artwork.show_id.in_(show_ids))
        )
        show_artworks = result.scalars().all()

        result = await db.execute(
            select(Artwork)
            .where(Artwork.episode_id.in_(episode.id for episode in episodes))
        ) if episodes else None
        episode_artworks = result.scalars().all() if result is not None else []

        # Build lookup: show_id -> {type: storage_key}
        show_artwork_map: dict[uuid.UUID, dict[str, str]] = defaultdict(dict)
        for aw in show_artworks:
            show_artwork_map[aw.show_id][aw.artwork_type] = aw.storage_key

        episode_artwork_map: dict[uuid.UUID, dict[str, str]] = defaultdict(dict)
        for aw in episode_artworks:
            episode_artwork_map[aw.episode_id][aw.artwork_type] = aw.storage_key

        # --- Index seasons by show_id ---
        seasons_by_show: dict[uuid.UUID, list[Season]] = defaultdict(list)
        for season in all_seasons:
            seasons_by_show[season.show_id].append(season)

        # --- Index episodes by season_id ---
        episodes_by_season: dict[uuid.UUID, list[Episode]] = defaultdict(list)
        for ep in episodes:
            episodes_by_season[ep.season_id].append(ep)

        # --- Build the catalogue structure ---
        # Section ordering follows reference.json order
        section_order = ["featured", "series", "minisodes", "songs"]
        sections: dict[str, list] = {}

        total_episodes = 0

        for show in shows:
            show_section = show.section
            if show_section not in sections:
                sections[show_section] = []

            show_seasons = seasons_by_show.get(show.id, [])

            # Separate Season 0 (trailers) from normal seasons
            trailers_season = None
            normal_seasons = []
            for s in show_seasons:
                if s.season_number == 0:
                    trailers_season = s
                else:
                    normal_seasons.append(s)

            # Build season entries
            season_entries = []
            for season in sorted(normal_seasons, key=lambda s: s.season_number):
                season_episodes = episodes_by_season.get(season.id, [])
                if not season_episodes:
                    continue

                # --- content_group collapsing ---
                # Episodes with the same content_group are language variants.
                # They collapse into ONE catalogue entry with a languages array.
                collapsed = CatalogueService._collapse_content_groups(
                    season_episodes,
                    episode_artwork_map,
                )
                total_episodes += len(collapsed)

                season_entries.append({
                    "season_number": season.season_number,
                    "episodes": collapsed,
                })

            # Build trailers if Season 0 exists and has published episodes
            trailer_entries = []
            if trailers_season:
                trailer_eps = episodes_by_season.get(trailers_season.id, [])
                if trailer_eps:
                    trailer_entries = CatalogueService._collapse_content_groups(
                        trailer_eps,
                        episode_artwork_map,
                    )

            show_entry: dict[str, Any] = {
                "slug": show.slug,
                "title": show.title,
                "section": show.section,
                "categories": sorted(show.categories) if show.categories else [],
                "synopsis": show.synopsis or "",
                "artwork": show_artwork_map.get(show.id, {}),
                "seasons": season_entries,
            }
            if trailer_entries:
                show_entry["trailers"] = trailer_entries

            sections.setdefault(show_section, []).append(show_entry)

        # Re-order sections by the canonical reference order
        ordered_sections: dict[str, list] = {}
        for sec in section_order:
            if sec in sections:
                # Sort shows within section by slug for determinism
                ordered_sections[sec] = sorted(
                    sections[sec], key=lambda s: s["slug"]
                )
        # Include any sections not in the canonical order (shouldn't happen, but safety)
        for sec in sorted(sections.keys()):
            if sec not in ordered_sections:
                ordered_sections[sec] = sorted(
                    sections[sec], key=lambda s: s["slug"]
                )

        catalogue = {
            "sections": ordered_sections,
        }

        stats = {
            "shows": len(shows),
            "episodes": total_episodes,
        }

        return catalogue, stats

    @staticmethod
    def _collapse_content_groups(
        episodes: list[Episode],
        episode_artwork_map: Optional[dict[uuid.UUID, dict[str, str]]] = None,
    ) -> list[dict[str, Any]]:
        """
        Collapse episodes sharing the same content_group into a single
        catalogue entry. The entry lists all available languages, sorted
        alphabetically. Duration is taken from the first language
        alphabetically (deterministic).
        """
        groups: dict[str, list[Episode]] = defaultdict(list)
        for ep in episodes:
            groups[ep.content_group].append(ep)

        collapsed = []
        # Sort groups by episode_number of the first variant, then by content_group for ties
        for cg_key in sorted(
            groups.keys(),
            key=lambda k: (groups[k][0].episode_number, k),
        ):
            variants = sorted(groups[cg_key], key=lambda e: e.language)
            primary = variants[0]  # First language alphabetically

            entry: dict[str, Any] = {
                "content_group": cg_key,
                "episode_number": primary.episode_number,
                "title": primary.title,
                "duration_seconds": primary.duration_seconds,
                "languages": [v.language for v in variants],
            }
            if episode_artwork_map:
                artwork = episode_artwork_map.get(primary.id, {})
                if artwork:
                    entry["artwork"] = artwork
            collapsed.append(entry)

        return collapsed

    @staticmethod
    async def get_live_catalogue(storage: StorageBackend) -> Optional[bytes]:
        """
        Retrieve the current live catalogue JSON bytes.
        Returns None if no catalogue has been published yet.
        """
        try:
            if await storage.exists(LIVE_CATALOGUE_KEY):
                return await storage.get(LIVE_CATALOGUE_KEY)
        except FileNotFoundError:
            pass
        return None
