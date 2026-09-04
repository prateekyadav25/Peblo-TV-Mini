import json
from collections import defaultdict
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.show import Show
from app.models.season import Season
from app.models.episode import Episode
from app.models.artwork import Artwork

def load_reference(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_seed(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

class SeedValidator:
    def __init__(self, ref_data, seed_data):
        self.ref_data = ref_data
        self.seed_data = seed_data
        
    def validate(self):
        errors = []
        warnings = []
        seen_content_languages = set()

        for row in self.seed_data:
            entity_name = row.get("episode_title") or row.get("show_title") or row.get("episode_id")
            section = row.get("section")
            status = row.get("status")
            if status == "published" and not section:
                errors.append({
                    "field": "section",
                    "episode_id": row.get("episode_id"),
                    "message": "Published content must have a section.",
                })
            elif status != "published" and not section:
                warnings.append({
                    "field": "section",
                    "episode_id": row.get("episode_id"),
                    "message": "Draft content has no section yet.",
                })

            key = (row.get("content_group"), row.get("language"))
            if key in seen_content_languages:
                errors.append({
                    "field": "content_group + language",
                    "episode_id": row.get("episode_id"),
                    "message": "The content group and language combination is duplicated.",
                })
            seen_content_languages.add(key)

            if status == "published" and not row.get("artwork_available"):
                errors.append({
                    "field": "artwork_available",
                    "episode_id": row.get("episode_id"),
                    "message": "Published content must have artwork.",
                })

            episode_title = row.get("episode_title")
            if episode_title and episode_title == episode_title.upper() and any(char.isalpha() for char in episode_title):
                warnings.append({
                    "field": "episode_title",
                    "episode_id": row.get("episode_id"),
                    "message": "Episode title is all uppercase; use editor-friendly title casing.",
                })

        return {"errors": errors, "warnings": warnings}

class DBValidator:
    @staticmethod
    async def generate_report(db: AsyncSession) -> Dict[str, List[Dict[str, str]]]:
        errors = []

        def _add_error(entity_type, entity_id, name, problem, fix):
            errors.append({
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "entity_name": name,
                "problem": problem,
                "fix": fix
            })

        # 1. Check Shows
        result = await db.execute(select(Show))
        shows = result.scalars().all()
        
        for show in shows:
            if show.status == 'published' and not show.section:
                _add_error(
                    "Show", show.id, show.title,
                    "Published show is missing a section.",
                    "Assign a valid section to the show or unpublish it."
                )
            if show.status == 'published' and not show.categories:
                _add_error(
                    "Show", show.id, show.title,
                    "Show has no categories.",
                    "Assign at least one category."
                )

        # 2. Check Artwork
        result = await db.execute(select(Artwork))
        artworks = result.scalars().all()
        
        show_artworks = defaultdict(set)
        episode_artworks = defaultdict(set)
        for aw in artworks:
            if aw.show_id:
                show_artworks[aw.show_id].add(aw.artwork_type)
            if aw.episode_id:
                episode_artworks[aw.episode_id].add(aw.artwork_type)

        for show in shows:
            if show.status == 'published':
                available = show_artworks[show.id]
                required = {"poster", "banner", "thumbnail"}
                missing = required - available
                if missing:
                    _add_error(
                        "Show", show.id, show.title,
                        f"Published show is missing artwork: {', '.join(missing)}.",
                        f"Upload the missing artwork ({', '.join(missing)})."
                    )

        # 3. Check Episodes
        result = await db.execute(select(Episode))
        episodes = result.scalars().all()
        result = await db.execute(select(Season))
        seasons = {season.id: season for season in result.scalars().all()}
        published_show_ids = {show.id for show in shows if show.status == 'published'}
        
        cg_langs = set()
        for ep in episodes:
            cg_lang_key = (ep.content_group, ep.language)
            if cg_lang_key in cg_langs:
                _add_error(
                    "Episode", ep.id, ep.title,
                    f"Duplicate language '{ep.language}' for content group '{ep.content_group}'.",
                    "Delete or edit the duplicate episode."
                )
            cg_langs.add(cg_lang_key)

            season = seasons.get(ep.season_id)
            validates_for_publish = season is not None and season.show_id in published_show_ids
            if ep.status == 'published' and validates_for_publish:
                if not ep.duration_seconds:
                    _add_error(
                        "Episode", ep.id, ep.title,
                        "Published episode is missing a duration.",
                        "Set a valid duration in seconds or unpublish the episode."
                    )
                # Ensure episode has artwork if required by your interpretation
                # (We added episode_id to Artwork for this)
                available = episode_artworks[ep.id]
                if not available:
                    _add_error(
                        "Episode", ep.id, ep.title,
                        "Published episode is missing artwork.",
                        "Upload artwork for the episode or unpublish it."
                    )

        # Group blocking issues into useful categories is requested by prompt, but we return a flat list for now or group them.
        # Let's group them:
        grouped = {
            "publication_requirements": [],
            "missing_required_metadata": [],
            "duplicate_content": [],
            "invalid_artwork": []
        }
        
        for err in errors:
            if "missing artwork" in err["problem"]:
                grouped["invalid_artwork"].append(err)
            elif "Duplicate" in err["problem"]:
                grouped["duplicate_content"].append(err)
            elif "section" in err["problem"] or "duration" in err["problem"]:
                grouped["publication_requirements"].append(err)
            else:
                grouped["missing_required_metadata"].append(err)

        return {"categories": grouped, "total_errors": len(errors)}
