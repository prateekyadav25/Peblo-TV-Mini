import json
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from app.storage.base import StorageBackend
from app.services.catalogue_service import CatalogueService, LIVE_CATALOGUE_KEY

class SearchService:
    _catalogue_cache: dict[str, tuple[str | None, Dict[str, Any]]] = {}

    @staticmethod
    def _normalize(text: Optional[str]) -> str:
        if not text:
            return ""
        return " ".join(text.lower().split())

    @staticmethod
    async def search(
        storage: StorageBackend,
        q: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        section: Optional[str] = None
    ) -> Dict[str, Any]:
        version = await storage.get_version(LIVE_CATALOGUE_KEY)
        cache_key = getattr(storage, "base_path", storage.__class__.__name__)
        cached = SearchService._catalogue_cache.get(cache_key)
        if cached and cached[0] == version:
            catalogue = cached[1]
        else:
            data_bytes = await CatalogueService.get_live_catalogue(storage)
            if not data_bytes:
                raise HTTPException(status_code=503, detail="Catalogue unavailable")

            try:
                catalogue = json.loads(data_bytes)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid catalogue format")
            SearchService._catalogue_cache[cache_key] = (version, catalogue)

        if not catalogue:
            raise HTTPException(status_code=503, detail="Catalogue unavailable")

        q_norm = SearchService._normalize(q)
        cat_norm = SearchService._normalize(category)
        lang_norm = SearchService._normalize(language)
        sec_norm = SearchService._normalize(section)

        results = []

        for sec, shows in catalogue.get("sections", {}).items():
            if sec_norm and sec_norm != SearchService._normalize(sec):
                continue

            for show in shows:
                show_matches = True
                
                # Filter by category
                if cat_norm:
                    show_cats = [SearchService._normalize(c) for c in show.get("categories", [])]
                    if cat_norm not in show_cats:
                        show_matches = False

                # We need to filter seasons/episodes by language and q
                matching_seasons = []
                show_title_match = q_norm and q_norm in SearchService._normalize(show.get("title"))
                category_match = any(
                    q_norm in SearchService._normalize(category_name)
                    for category_name in show.get("categories", [])
                ) if q_norm else False

                for season in show.get("seasons", []):
                    matching_episodes = []
                    for ep in season.get("episodes", []):
                        ep_lang_match = True
                        if lang_norm:
                            ep_langs = [SearchService._normalize(l) for l in ep.get("languages", [])]
                            if lang_norm not in ep_langs:
                                ep_lang_match = False

                        ep_title_match = q_norm and q_norm in SearchService._normalize(ep.get("title"))
                        
                        # Query matches if it matches show title OR episode title
                        ep_q_match = True
                        if q_norm:
                            if not (show_title_match or category_match or ep_title_match):
                                ep_q_match = False

                        if ep_lang_match and ep_q_match:
                            # If language filter is applied, only return that language in the list
                            filtered_ep = ep.copy()
                            if lang_norm:
                                filtered_ep["languages"] = [l for l in ep.get("languages", []) if SearchService._normalize(l) == lang_norm]
                            matching_episodes.append(filtered_ep)

                    if matching_episodes:
                        season_copy = season.copy()
                        season_copy["episodes"] = matching_episodes
                        matching_seasons.append(season_copy)

                # Trailer filtering (Season 0)
                matching_trailers = []
                for trailer in show.get("trailers", []):
                    tr_lang_match = True
                    if lang_norm:
                        tr_langs = [SearchService._normalize(l) for l in trailer.get("languages", [])]
                        if lang_norm not in tr_langs:
                            tr_lang_match = False

                    tr_title_match = q_norm and q_norm in SearchService._normalize(trailer.get("title"))
                    tr_q_match = True
                    if q_norm:
                        if not (show_title_match or category_match or tr_title_match):
                            tr_q_match = False

                    if tr_lang_match and tr_q_match:
                        filtered_tr = trailer.copy()
                        if lang_norm:
                            filtered_tr["languages"] = [l for l in trailer.get("languages", []) if SearchService._normalize(l) == lang_norm]
                        matching_trailers.append(filtered_tr)

                # A show is included if it matches category and has matching content
                # If there was no q or lang filter, all episodes match. If show_matches is false (due to category), we skip.
                if show_matches and (matching_seasons or matching_trailers):
                    show_copy = show.copy()
                    show_copy["seasons"] = matching_seasons
                    if matching_trailers:
                        show_copy["trailers"] = matching_trailers
                    elif "trailers" in show_copy:
                        del show_copy["trailers"]
                    results.append(show_copy)

        return {"results": results}
