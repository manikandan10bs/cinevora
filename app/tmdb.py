"""
Cinevora TMDB Integration Service
Provides verified movie metadata, official YouTube trailer video keys,
posters, and backdrops directly from The Movie Database (TMDB) API v3.
Acts as Cinevora's PRIMARY movie dataset provider, with Master_Movies fallback.
"""

import logging
import re
from typing import Optional, Dict, Any, List
import requests

from app.config import settings

logger = logging.getLogger("cinevora.tmdb")

TMDB_GENRES = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Sci-Fi",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}


class TmdbClient:
    """Client for querying The Movie Database (TMDB) API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.get_tmdb_api_key()
        self.base_url = settings.TMDB_BASE_URL.rstrip("/")
        self.image_base = settings.TMDB_IMAGE_BASE.rstrip("/")
        self._cache_trending: Optional[List[Dict[str, Any]]] = None
        self._cache_popular: Optional[List[Dict[str, Any]]] = None
        self._cache_top_rated: Optional[List[Dict[str, Any]]] = None

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

    def get_movie_details_with_credits(self, tmdb_id: int | str) -> Optional[Dict[str, Any]]:
        """
        Fetches full movie details including credits (director, cast) and videos.
        """
        if not self.is_configured:
            return None

        return self._get(f"movie/{tmdb_id}", {"append_to_response": "credits,videos"})

    def get_popular_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Fetches popular movies currently from TMDB."""
        if not self.is_configured:
            return []
        if page == 1 and self._cache_popular is not None:
            return self._cache_popular

        data = self._get("movie/popular", {"page": page})
        results = data.get("results", []) if data else []
        if page == 1:
            self._cache_popular = results
        return results

    def get_trending_movies(self, time_window: str = "week", page: int = 1) -> List[Dict[str, Any]]:
        """Fetches trending movies from TMDB."""
        if not self.is_configured:
            return []
        if page == 1 and self._cache_trending is not None:
            return self._cache_trending

        data = self._get(f"trending/movie/{time_window}", {"page": page})
        results = data.get("results", []) if data else []
        if page == 1:
            self._cache_trending = results
        return results

    def get_top_rated_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Fetches top-rated cinema classics from TMDB."""
        if not self.is_configured:
            return []
        if page == 1 and self._cache_top_rated is not None:
            return self._cache_top_rated

        data = self._get("movie/top_rated", {"page": page})
        results = data.get("results", []) if data else []
        if page == 1:
            self._cache_top_rated = results
        return results

    def format_image_url(self, path: Optional[str], size: str = "w500") -> Optional[str]:
        """
        Builds absolute TMDB image URL for poster or backdrop.
        Example sizes: 'w500', 'w1280', 'original'.
        """
        if not path:
            return None
        clean_path = path.lstrip("/")
        return f"{self.image_base}/{size}/{clean_path}"

    def convert_tmdb_to_movie_dict(self, m: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw TMDB movie object into Cinevora standard MovieItem dict.
        """
        tmdb_id = m.get("id")
        title = m.get("title") or m.get("original_title") or "Untitled Movie"
        rel_date = m.get("release_date") or ""
        year = rel_date[:4] if len(rel_date) >= 4 else "2024"
        vote_avg = float(m.get("vote_average", 7.5))
        lang = m.get("original_language", "en")

        genre_names = []
        if "genres" in m and isinstance(m["genres"], list):
            genre_names = [g.get("name") for g in m["genres"] if g.get("name")]
        elif "genre_ids" in m and isinstance(m["genre_ids"], list):
            genre_names = [TMDB_GENRES.get(gid) for gid in m["genre_ids"] if TMDB_GENRES.get(gid)]
        genres_str = ", ".join(genre_names) if genre_names else "Cinema"

        poster_url = self.format_image_url(m.get("poster_path"), "w500") or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500"
        backdrop_url = self.format_image_url(m.get("backdrop_path"), "w1280") or poster_url

        # Check for director/cast in credits if appended
        director = "Visionary Director"
        cast_str = "Ensemble Cast"
        credits = m.get("credits")
        if credits and isinstance(credits, dict):
            crew = credits.get("crew", [])
            for c in crew:
                if c.get("job") == "Director":
                    director = c.get("name", director)
                    break
            cast = credits.get("cast", [])
            if cast:
                cast_str = ", ".join([actor.get("name") for actor in cast[:4] if actor.get("name")])

        # Trailer check
        trailer_url = None
        if "videos" in m and isinstance(m["videos"], dict):
            vids = m["videos"].get("results", [])
            for v in vids:
                if v.get("site") == "YouTube" and v.get("type") == "Trailer" and v.get("key"):
                    trailer_url = f"https://www.youtube.com/watch?v={v['key']}"
                    break

        return {
            "movie_id": f"TMDB-{tmdb_id}",
            "catalog_id": f"TMDB-{tmdb_id}",
            "title": title,
            "movie_title": title,
            "release_date": rel_date,
            "release_year": year,
            "genres": genres_str,
            "score": round(vote_avg / 10.0, 2),
            "predicted_rating": round(vote_avg, 1),
            "cinema_region": "Hollywood" if lang == "en" else "International",
            "original_language": lang,
            "poster_url": poster_url,
            "movie_poster": poster_url,
            "backdrop_url": backdrop_url,
            "trailer_url": trailer_url,
            "trailer_link": trailer_url,
            "synopsis": m.get("overview") or f"Directed by {director}. Starring {cast_str}.",
            "director": director,
            "cast": cast_str,
            "tmdb_id": tmdb_id,
            "dataset_source": "tmdb"
        }


# Global singleton instance
tmdb_client = TmdbClient()
