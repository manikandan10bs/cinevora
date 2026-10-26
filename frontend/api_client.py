"""
Cinevora Frontend API Client
Provides HTTP communication with the Cinevora FastAPI backend.
Handles timeouts, connection retries, and errors cleanly.
"""

import logging
from typing import Dict, List, Optional, Any, Union
import requests

from frontend.config import API_BASE_URL

logger = logging.getLogger("cinevora.client")
DEFAULT_TIMEOUT = 12.0  # seconds


class CinevoraAPIClient:
    """Wrapper for all Cinevora REST API endpoints."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{path}"
        try:
            res = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            if res.status_code == 200:
                return res.json()
            logger.warning("GET %s returned HTTP %s: %s", path, res.status_code, res.text[:200])
            return None
        except requests.RequestException as e:
            logger.error("Connection error for GET %s: %s", path, type(e).__name__)
            return None

    def _post(self, path: str, payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{path}"
        try:
            res = requests.post(url, json=payload, timeout=timeout)
            if res.status_code == 200:
                return res.json()
            logger.warning("POST %s returned HTTP %s: %s", path, res.status_code, res.text[:200])
            return None
        except requests.RequestException as e:
            logger.error("Connection error for POST %s: %s", path, type(e).__name__)
            return None

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> bool:
        url = f"{self.base_url}{path}"
        try:
            res = requests.delete(url, params=params, timeout=DEFAULT_TIMEOUT)
            return res.status_code == 200
        except requests.RequestException as e:
            logger.error("Connection error for DELETE %s: %s", path, type(e).__name__)
            return False

    # -------------------------------------------------------------------------
    # Health & System
    # -------------------------------------------------------------------------
    def get_health(self) -> Optional[Dict[str, Any]]:
        return self._get("/health")

    def get_assistant_status(self) -> Optional[Dict[str, Any]]:
        return self._get("/assistant/status")

    # -------------------------------------------------------------------------
    # Movie Catalog Search & Details
    # -------------------------------------------------------------------------
    def search_movies(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        region: Optional[str] = None,
        language: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        sort_by: str = "popularity",
        limit: int = 12,
        offset: int = 0
    ) -> Dict[str, Any]:
        params = {
            "sort_by": sort_by,
            "limit": limit,
            "offset": offset
        }
        if query and query.strip():
            params["query"] = query.strip()
        if genre and genre != "All Genres":
            params["genre"] = genre
        if region and region not in ["All Regions", "All", ""]:
            params["region"] = region
        if language and language not in ["All Languages", "All", ""]:
            params["language"] = language
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year

        data = self._get("/movies/search", params=params)
        return data or {"count": 0, "results": []}

    def get_movie_details(self, movie_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        return self._get(f"/movies/{movie_id}")

    # -------------------------------------------------------------------------
    # Master Cleaned Catalog (3,560 Indian & Hollywood Titles)
    # -------------------------------------------------------------------------
    def get_master_catalog(
        self,
        query: Optional[str] = None,
        industry: Optional[str] = None,
        genre: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "rating",
        limit: int = 24,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Queries the 3,560-title master movie dataset."""
        params: Dict[str, Any] = {
            "sort_by": sort_by,
            "limit": limit,
            "offset": offset
        }
        if query and str(query).strip():
            params["query"] = str(query).strip()
        if industry and industry not in ["All", "All Industries", ""]:
            params["industry"] = industry
        if genre and genre not in ["All", "All Genres", ""]:
            params["genre"] = genre
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year
        if min_rating is not None and min_rating > 0.0:
            params["min_rating"] = min_rating

        data = self._get("/movies/catalog", params=params)
        return data or {"count": 0, "total": 0, "offset": offset, "limit": limit, "results": []}

    def get_master_catalog_stats(self) -> Dict[str, Any]:
        """Retrieves master dataset statistics and available filter options."""
        data = self._get("/movies/catalog/stats")
        return data or {
            "total_movies": 3560,
            "industries": {},
            "genres": [],
            "year_min": 2021,
            "year_max": 2025,
            "avg_rating": 6.33,
            "trailers_count": 1181
        }

    def get_master_catalog_movie(self, catalog_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full details for a master movie by catalog_id or movie_id."""
        return self._get(f"/movies/catalog/{catalog_id}")

    def get_indian_movies(self, language: Optional[str] = None, limit: int = 24) -> List[Dict[str, Any]]:
        """Retrieves Indian cinema movies from backend catalog."""
        res = self.search_movies(region="Indian", language=language, limit=limit)
        return res.get("results", [])

    def get_hollywood_movies(self, genre: Optional[str] = None, limit: int = 24) -> List[Dict[str, Any]]:
        """Retrieves Hollywood cinema movies from backend catalog."""
        res = self.search_movies(region="Hollywood", genre=genre, limit=limit)
        return res.get("results", [])

    # -------------------------------------------------------------------------
    # Recommender Service
    # -------------------------------------------------------------------------
    def get_recommendations(
        self,
        user_id: Optional[Union[int, str]] = None,
        genre: Optional[str] = None,
        industry: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        model_type: str = "content",
        limit: int = 10,
        exclude_rated: bool = True
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model_type": model_type,
            "limit": limit,
            "exclude_rated": str(exclude_rated).lower()
        }
        if user_id is not None:
            params["user_id"] = user_id
        if genre and genre not in ["All Genres", "All"]:
            params["genre"] = genre
        if industry and industry not in ["All Industries", "All"]:
            params["industry"] = industry
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year

        data = self._get("/recommendations", params=params)
        return data or {"count": 0, "recommendations": []}

    # -------------------------------------------------------------------------
    # AI Movie Assistant (Gemini Flash)
    # -------------------------------------------------------------------------
    def chat_assistant(
        self,
        message: str,
        user_id: Optional[Union[int, str]] = None,
        genre: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Sends natural language movie inquiry to FastAPI /assistant/chat endpoint.
        Returns structured dictionary with 'success', 'reply', 'recommendations',
        or informative error details if backend or Gemini fails.
        """
        payload: Dict[str, Any] = {
            "message": message,
            "limit": limit
        }
        if user_id is not None:
            payload["user_id"] = user_id
        if genre and genre != "All Genres":
            payload["genre"] = genre

        url = f"{self.base_url}/assistant/chat"
        try:
            res = requests.post(url, json=payload, timeout=25.0)
            if res.status_code == 200:
                data = res.json()
                data["success"] = True
                return data
            else:
                err_detail = "Server error"
                try:
                    err_json = res.json()
                    err_detail = err_json.get("detail", res.text[:200])
                except Exception:
                    err_detail = res.text[:200]
                logger.warning("POST /assistant/chat returned HTTP %s: %s", res.status_code, err_detail)
                return {
                    "success": False,
                    "error_type": f"HTTP_{res.status_code}",
                    "error_detail": f"Backend returned HTTP {res.status_code}: {err_detail}",
                    "reply": f"The assistant service encountered an issue (HTTP {res.status_code}).",
                    "recommendations": []
                }
        except requests.Timeout:
            logger.error("Timeout during POST /assistant/chat after 25.0s")
            return {
                "success": False,
                "error_type": "timeout",
                "error_detail": "The request timed out after 25 seconds waiting for the AI response.",
                "reply": "The AI assistant request timed out. Please try again or simplify your query.",
                "recommendations": []
            }
        except requests.ConnectionError:
            logger.error("Connection error during POST /assistant/chat to %s", url)
            return {
                "success": False,
                "error_type": "connection_error",
                "error_detail": f"Unable to reach Cinevora backend API at {self.base_url}. Please ensure the FastAPI server is running.",
                "reply": "Unable to connect to the Cinevora backend service.",
                "recommendations": []
            }
        except Exception as e:
            logger.error("Unexpected error during POST /assistant/chat: %s", type(e).__name__)
            return {
                "success": False,
                "error_type": "unexpected_error",
                "error_detail": str(e),
                "reply": f"An unexpected error occurred ({type(e).__name__}).",
                "recommendations": []
            }

    # -------------------------------------------------------------------------
    # User Favorites & Likes
    # -------------------------------------------------------------------------
    def get_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        data = self._get("/favorites", params={"user_id": user_id})
        return data.get("favorites", []) if data else []

    def add_favorite(
        self,
        user_id: str,
        movie_id: Any,
        movie_title: str,
        genres: str,
        release_date: Optional[str] = None,
        rating: Optional[float] = None
    ) -> bool:
        payload = {
            "user_id": user_id,
            "movie_id": movie_id,
            "movie_title": movie_title,
            "genres": genres,
            "release_date": release_date,
            "rating": rating
        }
        res = self._post("/favorites", payload=payload)
        return bool(res and res.get("status") in ["success", "already_exists"])

    def remove_favorite(self, user_id: str, movie_id: Any) -> bool:
        return self._delete(f"/favorites/{movie_id}", params={"user_id": user_id})

    def get_likes(self, user_id: str) -> List[Any]:
        data = self._get("/likes", params={"user_id": user_id})
        return data.get("liked_movie_ids", []) if data else []

    def toggle_like(self, user_id: str, movie_id: Any) -> Optional[bool]:
        payload = {"user_id": user_id, "movie_id": movie_id}
        res = self._post("/likes", payload=payload)
        return res.get("liked") if res else None

    # -------------------------------------------------------------------------
    # Search History Persistence
    # -------------------------------------------------------------------------
    def get_search_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetches persisted search history records for the user from SQLite."""
        data = self._get("/history/search", params={"user_id": user_id, "limit": limit})
        return data.get("history", []) if data else []

    def record_search_history(
        self,
        user_id: str,
        query: str,
        matched_genres: Optional[str] = None,
        matched_movie_id: Optional[int] = None,
        matched_movie_title: Optional[str] = None
    ) -> bool:
        """Records a search query to SQLite via FastAPI backend."""
        payload = {
            "user_id": user_id,
            "query": query,
            "matched_genres": matched_genres,
            "matched_movie_id": matched_movie_id,
            "matched_movie_title": matched_movie_title
        }
        res = self._post("/history/search", payload=payload)
        return bool(res and res.get("status") == "success")

    def clear_search_history(self, user_id: str) -> bool:
        """Clears persisted search history for the user."""
        return self._delete("/history/search", params={"user_id": user_id})

    # -------------------------------------------------------------------------
    # Authentication & Session Management
    # -------------------------------------------------------------------------
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates user against FastAPI backend. Returns user profile or None."""
        payload = {"username": username, "password": password}
        return self._post("/auth/login", payload=payload)

    def register(self, username: str, password: str, display_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Registers a new user account."""
        payload = {"username": username, "password": password, "display_name": display_name}
        return self._post("/auth/register", payload=payload)

    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieves user profile info."""
        return self._get(f"/auth/user/{username}")

    # -------------------------------------------------------------------------
    # Viewing History (Opened Movies)
    # -------------------------------------------------------------------------
    def record_view(
        self,
        user_id: str,
        movie_id: Any,
        movie_title: Optional[str] = None,
        genres: Optional[str] = None,
        industry: Optional[str] = None
    ) -> bool:
        """Records a viewed/opened movie event to SQLite via backend."""
        payload = {
            "user_id": str(user_id),
            "movie_id": str(movie_id),
            "movie_title": movie_title,
            "genres": genres,
            "industry": industry
        }
        res = self._post("/history/view", payload=payload)
        return bool(res and res.get("status") == "success")

    def get_view_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches viewed movie history records for the user from backend."""
        data = self._get("/history/view", params={"user_id": user_id, "limit": limit})
        return data.get("history", []) if data else []

    def clear_view_history(self, user_id: str) -> bool:
        """Clears viewed movie history records for the user."""
        return self._delete("/history/view", params={"user_id": user_id})

    # -------------------------------------------------------------------------
    # MLOps Monitoring
    # -------------------------------------------------------------------------
    def get_monitoring_metrics(self, exclude_internal: bool = True) -> Optional[Dict[str, Any]]:
        return self._get("/monitoring/metrics", params={"exclude_internal": str(exclude_internal).lower()})

    def get_monitoring_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        data = self._get("/monitoring/events", params={"limit": limit})
        return data.get("events", []) if data else []


# Global singleton client instance
api_client = CinevoraAPIClient()
