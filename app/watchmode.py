"""
Cinevora WatchMode Streaming Integration Service
Connects to WatchMode API v1 to fetch official streaming providers
(Netflix, Prime Video, Disney+, Apple TV, HBO Max, JioCinema, etc.)
with direct deep links and in-memory quota caching.
"""

import logging
import re
from typing import Optional, Dict, Any, List
import requests

from app.config import settings

logger = logging.getLogger("cinevora.watchmode")


class WatchmodeClient:
    """Client for querying WatchMode Streaming API v1."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.get_watchmode_api_key()
        self.base_url = settings.WATCHMODE_BASE_URL.rstrip("/")
        # In-memory LRU cache to conserve 2500 credit quota
        self._sources_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._id_cache: Dict[str, Optional[int]] = {}
        self._details_cache: Dict[str, Dict[str, Any]] = {}
        self._streaming_catalog_cache: Optional[List[Dict[str, Any]]] = None
        self._hero_movies_cache: Optional[List[Dict[str, Any]]] = None

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid WatchMode API key is provided."""
        return bool(self.api_key and len(self.api_key.strip()) >= 16)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Makes an authenticated GET request to the WatchMode API."""
        if not self.is_configured:
            return None

        clean_endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{clean_endpoint}"
        query_params = {"apiKey": self.api_key}
        if params:
            query_params.update(params)

        try:
            resp = requests.get(url, params=query_params, timeout=5.0)
            if resp.status_code == 200:
                return resp.json()
            logger.warning("WatchMode API request to %s failed (%d): %s", endpoint, resp.status_code, resp.text[:120])
            return None
        except Exception as e:
            logger.warning("WatchMode API request error on %s: %s", endpoint, e)
            return None

    def search_title_id(
        self,
        title: str,
        tmdb_id: Optional[int | str] = None,
        year: Optional[str] = None
    ) -> Optional[int]:
        """
        Finds WatchMode title ID for a movie.
        Prefers TMDB ID lookup, falls back to title search.
        """
        cache_key = f"tmdb:{tmdb_id}" if tmdb_id else f"name:{title.lower()}:{year or ''}"
        if cache_key in self._id_cache:
            return self._id_cache[cache_key]

        # 1. Search by TMDB ID if available
        if tmdb_id:
            data = self._get("search/", {
                "search_field": "tmdb_movie_id",
                "search_value": str(tmdb_id)
            })
            if data and data.get("title_results"):
                w_id = data["title_results"][0].get("id")
                if w_id:
                    self._id_cache[cache_key] = w_id
                    return w_id

        # 2. Search by title
        clean_title = re.sub(r"\(.*?\)", "", str(title)).strip()
        data = self._get("search/", {
            "search_field": "name",
            "search_value": clean_title,
            "types": "movie"
        })
        if data and data.get("title_results"):
            results = data["title_results"]
            # Match year if provided
            if year:
                clean_y = re.search(r"\b(19\d\d|20\d\d)\b", str(year))
                if clean_y:
                    y_int = int(clean_y.group(1))
                    for r in results:
                        if r.get("year") == y_int:
                            w_id = r.get("id")
                            self._id_cache[cache_key] = w_id
                            return w_id

            w_id = results[0].get("id")
            self._id_cache[cache_key] = w_id
            return w_id

        self._id_cache[cache_key] = None
        return None

    def get_sources_by_title_id(self, watchmode_id: int) -> List[Dict[str, Any]]:
        """
        Fetches active streaming sources for a WatchMode title ID.
        Deduplicates by service name, preferring subscription ('sub') / free.
        """
        cache_key = f"sources:{watchmode_id}"
        if cache_key in self._sources_cache:
            return self._sources_cache[cache_key]

        raw = self._get(f"title/{watchmode_id}/sources/")
        if not raw or not isinstance(raw, list):
            self._sources_cache[cache_key] = []
            return []

        seen_services = set()
        formatted: List[Dict[str, Any]] = []

        # Sort order: subscription first, then free, then rent/buy
        type_priority = {"sub": 0, "free": 1, "tve": 2, "rent": 3, "buy": 4}
        sorted_raw = sorted(raw, key=lambda x: type_priority.get(x.get("type", ""), 9))

        for s in sorted_raw:
            name = s.get("name")
            if not name:
                continue

            # Normalized deduplication
            norm_name = name.strip().lower()
            if norm_name in seen_services:
                continue
            seen_services.add(norm_name)

            web_url = s.get("web_url")
            # If deeplinks are blocked on free tiers, point to service search
            if not web_url or "Deeplinks" in web_url:
                web_url = f"https://www.google.com/search?q={requests.utils.quote(name + ' watch movie')}"

            formatted.append({
                "source_id": s.get("source_id"),
                "name": name,
                "type": s.get("type", "sub"),
                "region": s.get("region", "US"),
                "format": s.get("format", "HD"),
                "price": s.get("price"),
                "web_url": web_url,
            })

        self._sources_cache[cache_key] = formatted
        return formatted

    def get_streaming_sources_for_movie(
        self,
        title: str,
        tmdb_id: Optional[int | str] = None,
        year: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        High-level helper:
        Searches WatchMode title ID, then fetches and returns streaming sources.
        """
        if not self.is_configured:
            return []

        w_id = self.search_title_id(title, tmdb_id, year)
        sources = self.get_sources_by_title_id(w_id) if w_id else []

        # Fallback without year if year-filtered search had no sources
        if not sources and year:
            w_id_fallback = self.search_title_id(title, tmdb_id=None, year=None)
            if w_id_fallback and w_id_fallback != w_id:
                sources = self.get_sources_by_title_id(w_id_fallback)

        return sources

    def get_curated_streaming_catalog(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Retrieves top trending titles available for streaming right now.
        Cached in-memory to prevent burning quota.
        """
        if not self.is_configured:
            return []

        if self._streaming_catalog_cache is not None:
            return self._streaming_catalog_cache[:limit]

        data = self._get("list-titles/", {
            "types": "movie",
            "limit": limit,
            "sort_by": "popularity_desc"
        })

        if not data or not data.get("titles"):
            return []

        results = []
        for t in data["titles"][:limit]:
            results.append({
                "watchmode_id": t.get("id"),
                "title": t.get("title"),
                "year": t.get("year"),
                "imdb_id": t.get("imdb_id"),
                "tmdb_id": t.get("tmdb_id"),
                "type": "movie"
            })

        self._streaming_catalog_cache = results
        return results[:limit]

    def get_title_details(self, watchmode_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetches full title details including poster, backdrop, plot, and official trailer.
        """
        if not self.is_configured:
            return None
        cache_key = f"details:{watchmode_id}"
        if cache_key in self._details_cache:
            return self._details_cache[cache_key]

        data = self._get(f"title/{watchmode_id}/details/")
        if data and isinstance(data, dict):
            self._details_cache[cache_key] = data
            return data
        return None

    def get_hero_featured_movies(self, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Retrieves top trending titles from WatchMode with full details, backdrops,
        and verified YouTube trailer links for Cinevora's Hero Banner.
        """
        if not self.is_configured:
            return []

        if self._hero_movies_cache is not None:
            return self._hero_movies_cache[:limit]

        titles = self.get_curated_streaming_catalog(limit=limit)
        results = []

        for t in titles:
            w_id = t.get("watchmode_id")
            if not w_id:
                continue
            details = self.get_title_details(w_id)
            if not details:
                continue

            trailer_url = details.get("trailer")
            poster = details.get("posterLarge") or details.get("poster")
            backdrop = details.get("backdrop") or poster
            genres = ", ".join(details.get("genre_names", ["Cinema"]))
            lang = details.get("original_language", "en")

            results.append({
                "movie_id": f"WM-{w_id}",
                "catalog_id": f"WM-{w_id}",
                "movie_title": details.get("title") or t.get("title", "Featured Cinema"),
                "title": details.get("title") or t.get("title", "Featured Cinema"),
                "release_date": details.get("release_date") or str(details.get("year", "2026")),
                "release_year": str(details.get("year", "2026")),
                "genres": genres,
                "score": 1.0,
                "predicted_rating": float(details.get("user_rating") or 8.5),
                "cinema_region": "Hollywood" if lang == "en" else "International",
                "original_language": lang,
                "poster_url": poster,
                "backdrop_url": backdrop,
                "trailer_url": trailer_url,
                "trailer_link": trailer_url,
                "synopsis": details.get("plot_overview") or "A celebrated cinema premiere on Cinevora.",
                "dataset_source": "watchmode"
            })

        if results:
            self._hero_movies_cache = results

        return results[:limit]

    def get_trailer_by_title_or_id(
        self,
        title: str,
        tmdb_id: Optional[int | str] = None,
        year: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetches the official trailer watch link from WatchMode.
        """
        if not self.is_configured:
            return None
        w_id = self.search_title_id(title, tmdb_id, year)
        if not w_id:
            return None
        details = self.get_title_details(w_id)
        if details and details.get("trailer"):
            return details["trailer"]
        return None


# Global singleton instance
watchmode_client = WatchmodeClient()
