"""
Cinevora TMDB Integration Service
Provides verified movie metadata, official YouTube trailer video keys,
posters, and backdrops directly from The Movie Database (TMDB) API v3.
"""

import logging
import re
from typing import Optional, Dict, Any, List
import requests

from app.config import settings

logger = logging.getLogger("cinevora.tmdb")


class TmdbClient:
    """Client for querying The Movie Database (TMDB) API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.get_tmdb_api_key()
        self.base_url = settings.TMDB_BASE_URL.rstrip("/")
        self.image_base = settings.TMDB_IMAGE_BASE.rstrip("/")

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid TMDB API key is provided."""
        return bool(self.api_key and len(self.api_key.strip()) >= 16)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Makes an authenticated GET request to the TMDB API."""
        if not self.is_configured:
            return None

        clean_endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{clean_endpoint}"
        query_params = {"api_key": self.api_key}
        if params:
            query_params.update(params)

        try:
            resp = requests.get(url, params=query_params, timeout=5.0)
            if resp.status_code == 200:
                return resp.json()
            logger.warning("TMDB API request to %s failed with status %d: %s", endpoint, resp.status_code, resp.text[:120])
            return None
        except Exception as e:
            logger.warning("TMDB API request error on %s: %s", endpoint, e)
            return None

    def search_movie(self, title: str, year: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Searches TMDB for movies matching title and optional release year.
        """
        if not self.is_configured:
            return []

        clean_title = re.sub(r"\(.*?\)", "", str(title)).strip()
        params: Dict[str, Any] = {"query": clean_title, "include_adult": False}

        if year:
            clean_year = re.search(r"\b(19\d\d|20\d\d)\b", str(year))
            if clean_year:
                params["year"] = clean_year.group(1)

        data = self._get("search/movie", params)
        if not data or "results" not in data:
            return []

        return data.get("results", [])

    def get_movie_videos(self, tmdb_id: int | str) -> List[Dict[str, Any]]:
        """
        Fetches trailers, teasers, and clips for a TMDB movie ID.
        """
        if not self.is_configured:
            return []

        data = self._get(f"movie/{tmdb_id}/videos")
        if not data or "results" not in data:
            return []

        return data.get("results", [])

    def get_official_trailer_url(self, tmdb_id: int | str) -> Optional[str]:
        """
        Extracts the official YouTube trailer watch link for a given TMDB movie ID.
        Prefers Type='Trailer', Site='YouTube', and official=True.
        """
        videos = self.get_movie_videos(tmdb_id)
        if not videos:
            return None

        # Pass 1: Official Trailer on YouTube
        for v in videos:
            if (
                v.get("site") == "YouTube"
                and v.get("type") == "Trailer"
                and v.get("official") is True
                and v.get("key")
            ):
                return f"https://www.youtube.com/watch?v={v['key']}"

        # Pass 2: Any Trailer on YouTube
        for v in videos:
            if v.get("site") == "YouTube" and v.get("type") == "Trailer" and v.get("key"):
                return f"https://www.youtube.com/watch?v={v['key']}"

        # Pass 3: Any Teaser or Clip on YouTube
        for v in videos:
            if v.get("site") == "YouTube" and v.get("key"):
                return f"https://www.youtube.com/watch?v={v['key']}"

        return None

    def resolve_trailer_by_title(self, title: str, year: Optional[str] = None) -> Optional[str]:
        """
        High-level resolver:
        1. Searches TMDB for movie by title & year.
        2. Retrieves official YouTube trailer from TMDB videos.
        3. Falls back to search without year if year-filtered search yields no trailer.
        Returns YouTube watch URL or None.
        """
        if not self.is_configured:
            return None

        # 1. Search with year if present
        results = self.search_movie(title, year)
        for movie in results[:3]:
            tmdb_id = movie.get("id")
            if tmdb_id:
                trailer = self.get_official_trailer_url(tmdb_id)
                if trailer:
                    logger.info("Found TMDB trailer for '%s' (TMDB ID %s): %s", title, tmdb_id, trailer)
                    return trailer

        # 2. Fallback: Search without year (handles re-releases, festivals, year mismatches)
        if year:
            results_no_year = self.search_movie(title)
            for movie in results_no_year[:3]:
                tmdb_id = movie.get("id")
                if tmdb_id:
                    trailer = self.get_official_trailer_url(tmdb_id)
                    if trailer:
                        logger.info("Found TMDB trailer without year for '%s' (TMDB ID %s): %s", title, tmdb_id, trailer)
                        return trailer

        return None

    def get_movie_details(self, tmdb_id: int | str) -> Optional[Dict[str, Any]]:
        """
        Fetches full movie details including runtime, genres, poster, and backdrop.
        """
        if not self.is_configured:
            return None

        return self._get(f"movie/{tmdb_id}")

    def format_image_url(self, path: Optional[str], size: str = "w500") -> Optional[str]:
        """
        Builds absolute TMDB image URL for poster or backdrop.
        Example sizes: 'w500', 'w1280', 'original'.
        """
        if not path:
            return None
        clean_path = path.lstrip("/")
        return f"{self.image_base}/{size}/{clean_path}"


# Global singleton instance
tmdb_client = TmdbClient()
