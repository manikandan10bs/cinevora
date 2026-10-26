"""
Cinevora SQLite Database & Telemetry Storage Module
Handles persistence for:
1. User Favorites and Likes (Application User interactions)
2. Live API Request Telemetry & Monitoring Events
"""

import sqlite3
import datetime
import logging
import hashlib
import secrets
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from app.config import settings

logger = logging.getLogger("cinevora.db")

# Default database path
DB_DIR = settings.PROJECT_ROOT_PATH / "data"
DB_PATH = DB_DIR / "cinevora.db"


def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory enabled."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initializes database tables and performance indices if they do not exist.
    Safe to run repeatedly.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. User Favorites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                movie_id INTEGER NOT NULL,
                movie_title TEXT NOT NULL,
                genres TEXT NOT NULL,
                release_date TEXT,
                rating REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, movie_id)
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fav_user ON favorites(user_id);")

        # 2. User Likes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                movie_id INTEGER NOT NULL,
                liked INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, movie_id)
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_user ON likes(user_id);")

        # 3. Live Monitoring & Telemetry Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                duration_ms REAL NOT NULL,
                event_type TEXT NOT NULL DEFAULT 'api_request',
                genre_filter TEXT,
                user_id TEXT,
                model_type TEXT,
                assistant_mode TEXT,
                items_count INTEGER,
                error_category TEXT,
                is_internal INTEGER NOT NULL DEFAULT 0
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON monitoring_events(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ep ON monitoring_events(endpoint);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON monitoring_events(event_type);")

        # 4. User Search History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                matched_genres TEXT,
                matched_movie_id INTEGER,
                matched_movie_title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_user ON search_history(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_created ON search_history(created_at);")

        # 5. Users table for authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")

        # 6. Viewed / Opened Movie Interactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS view_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                movie_id TEXT NOT NULL,
                movie_title TEXT,
                genres TEXT,
                industry TEXT,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_view_user ON view_history(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_view_time ON view_history(viewed_at);")

        conn.commit()

    # Idempotently seed development demo account
    seed_default_users()
    logger.info("Database initialized at %s", DB_PATH)


# -----------------------------------------------------------------------------
# User Authentication & Credentials Management
# -----------------------------------------------------------------------------
def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes a password with PBKDF2-HMAC-SHA256 and a 16-byte cryptographically secure salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return key.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a password against a stored hash and salt using constant-time comparison."""
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return secrets.compare_digest(key.hex(), stored_hash)


def create_user(
    username: str,
    password: str,
    display_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Creates a new user record with hashed password. Returns safe user dict or None if exists."""
    clean_username = username.strip().lower()
    if not clean_username or not password:
        return None
    pwd_hash, salt = hash_password(password)
    disp = display_name.strip() if display_name else clean_username
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, display_name)
                VALUES (?, ?, ?, ?);
            """, (clean_username, pwd_hash, salt, disp))
            conn.commit()
            user_id = cursor.lastrowid
            return {
                "id": user_id,
                "username": clean_username,
                "display_name": disp,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
    except sqlite3.IntegrityError:
        return None
    except Exception as e:
        logger.error("Error creating user %s: %s", clean_username, e)
        return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Retrieves user record by username."""
    clean_username = username.strip().lower()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, salt, display_name, created_at
                FROM users
                WHERE username = ?;
            """, (clean_username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error("Error fetching user %s: %s", clean_username, e)
        return None


def verify_user_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verifies credentials. Returns safe user dictionary without sensitive hash/salt."""
    user = get_user_by_username(username)
    if not user:
        return None
    if verify_password(password, user["password_hash"], user["salt"]):
        return {
            "id": user["id"],
            "username": user["username"],
            "display_name": user.get("display_name") or user["username"],
            "created_at": user.get("created_at")
        }
    return None


def seed_default_users() -> None:
    """Idempotently seeds the requested development demo account (test_id_1 / test123)."""
    try:
        demo_user = get_user_by_username("test_id_1")
        if not demo_user:
            create_user(
                username="test_id_1",
                password="test123",
                display_name="Cinevora Demo Explorer"
            )
            logger.info("Seeded default demo account 'test_id_1'.")
    except Exception as e:
        logger.warning("Could not seed default demo user: %s", e)


# -----------------------------------------------------------------------------
# Viewing History & Opened Movie Tracking
# -----------------------------------------------------------------------------
def record_view_history(
    user_id: str,
    movie_id: Any,
    movie_title: Optional[str] = None,
    genres: Optional[str] = None,
    industry: Optional[str] = None
) -> bool:
    """Records a viewed/opened movie interaction for personalized recommendations."""
    clean_user = str(user_id).strip()
    norm_mid = _normalize_movie_id(movie_id)
    if not clean_user or not norm_mid:
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO view_history (user_id, movie_id, movie_title, genres, industry)
                VALUES (?, ?, ?, ?, ?);
            """, (clean_user, str(norm_mid), movie_title, genres, industry))
            conn.commit()
            return True
    except Exception as e:
        logger.error("Error recording view history for %s: %s", clean_user, e)
        return False


def get_view_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent view history records for user, ordered by most recent."""
    clean_user = str(user_id).strip()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, movie_id, movie_title, genres, industry, viewed_at
                FROM view_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?;
            """, (clean_user, limit))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error("Error fetching view history for %s: %s", clean_user, e)
        return []


def clear_view_history(user_id: str) -> bool:
    """Clears viewing history for user."""
    clean_user = str(user_id).strip()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM view_history WHERE user_id = ?;", (clean_user,))
            conn.commit()
            return True
    except Exception as e:
        logger.error("Error clearing view history for %s: %s", clean_user, e)
        return False


# -----------------------------------------------------------------------------
# Favorites CRUD Operations
# -----------------------------------------------------------------------------
def _normalize_movie_id(movie_id: Any) -> Any:
    """Safely normalizes movie_id: returns int if digits, else stripped string."""
    if isinstance(movie_id, int):
        return movie_id
    if isinstance(movie_id, str) and movie_id.isdigit():
        return int(movie_id)
    return str(movie_id).strip()


def add_favorite(
    user_id: str,
    movie_id: Union[int, str],
    movie_title: str,
    genres: str,
    release_date: Optional[str] = None,
    rating: Optional[float] = None
) -> bool:
    """
    Adds a movie to the user's favorites.
    Supports both MovieLens integer IDs and Master Catalog string IDs (e.g. CINEVORA-0000001).
    Returns True if added, False if it was already in favorites.
    """
    try:
        norm_id = _normalize_movie_id(movie_id)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO favorites (user_id, movie_id, movie_title, genres, release_date, rating)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (str(user_id), norm_id, movie_title, genres, release_date, rating))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error("Error adding favorite: %s", e)
        return False


def remove_favorite(user_id: str, movie_id: Union[int, str]) -> bool:
    """Removes a movie from the user's favorites."""
    try:
        norm_id = _normalize_movie_id(movie_id)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM favorites WHERE user_id = ? AND movie_id = ?;
            """, (str(user_id), norm_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error("Error removing favorite: %s", e)
        return False


def get_favorites(user_id: str) -> List[Dict[str, Any]]:
    """Returns a list of all favorite movies for a given user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, movie_id, movie_title, genres, release_date, rating, created_at
                FROM favorites
                WHERE user_id = ?
                ORDER BY created_at DESC;
            """, (str(user_id),))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Error getting favorites: %s", e)
        return []


def is_favorite(user_id: str, movie_id: Union[int, str]) -> bool:
    """Checks whether a specific movie is favorited by the user."""
    try:
        norm_id = _normalize_movie_id(movie_id)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM favorites WHERE user_id = ? AND movie_id = ? LIMIT 1;
            """, (str(user_id), norm_id))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error("Error checking favorite: %s", e)
        return False


# -----------------------------------------------------------------------------
# Likes CRUD Operations
# -----------------------------------------------------------------------------
def add_like(user_id: str, movie_id: Union[int, str]) -> bool:
    """Explicitly adds a like for a movie (idempotent, does not toggle off)."""
    try:
        norm_id = _normalize_movie_id(movie_id)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO likes (user_id, movie_id, liked) VALUES (?, ?, 1);
            """, (str(user_id), norm_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error("Error adding like: %s", e)
        return False


def toggle_like(user_id: str, movie_id: Union[int, str]) -> Tuple[bool, bool]:
    """
    Toggles the like state of a movie for a user.
    Supports both MovieLens integer IDs and Master Catalog string IDs (e.g. CINEVORA-0000001).
    Returns: (success, currently_liked)
    """
    try:
        norm_id = _normalize_movie_id(movie_id)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT liked FROM likes WHERE user_id = ? AND movie_id = ?;
            """, (str(user_id), norm_id))
            row = cursor.fetchone()

            if row is None:
                # Insert like
                cursor.execute("""
                    INSERT INTO likes (user_id, movie_id, liked) VALUES (?, ?, 1);
                """, (str(user_id), norm_id))
                conn.commit()
                return True, True
            else:
                # Toggle
                new_state = 0 if row["liked"] == 1 else 1
                cursor.execute("""
                    UPDATE likes SET liked = ? WHERE user_id = ? AND movie_id = ?;
                """, (new_state, str(user_id), norm_id))
                conn.commit()
                return True, (new_state == 1)
    except Exception as e:
        logger.error("Error toggling like: %s", e)
        return False, False


def get_user_likes(user_id: str) -> List[Any]:
    """Returns a list of movie IDs liked by the user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT movie_id FROM likes WHERE user_id = ? AND liked = 1;
            """, (str(user_id),))
            rows = cursor.fetchall()
            return [row["movie_id"] for row in rows]
    except Exception as e:
        logger.error("Error fetching likes: %s", e)
        return []


# -----------------------------------------------------------------------------
# User Search History CRUD Operations
# -----------------------------------------------------------------------------
def record_search_history(
    user_id: str,
    query: str,
    matched_genres: Optional[str] = None,
    matched_movie_id: Optional[int] = None,
    matched_movie_title: Optional[str] = None
) -> bool:
    """
    Records a user's search query and matched metadata into SQLite.
    Binds the history to the active user persona.
    """
    if not query or not query.strip():
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_history (user_id, query, matched_genres, matched_movie_id, matched_movie_title)
                VALUES (?, ?, ?, ?, ?);
            """, (str(user_id), query.strip(), matched_genres, matched_movie_id, matched_movie_title))
            conn.commit()
            return True
    except Exception as e:
        logger.error("Error recording search history: %s", e)
        return False


def get_search_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Returns the most recent search history records for a user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, query, matched_genres, matched_movie_id, matched_movie_title, created_at
                FROM search_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?;
            """, (str(user_id), limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Error fetching search history: %s", e)
        return []


def clear_search_history(user_id: str) -> bool:
    """Clears all search history records for a specific user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM search_history WHERE user_id = ?;
            """, (str(user_id),))
            conn.commit()
            return True
    except Exception as e:
        logger.error("Error clearing search history: %s", e)
        return False


# -----------------------------------------------------------------------------
# Live Monitoring & Telemetry Recording
# -----------------------------------------------------------------------------
def record_event(
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    event_type: str = "api_request",
    genre_filter: Optional[str] = None,
    user_id: Optional[str] = None,
    model_type: Optional[str] = None,
    assistant_mode: Optional[str] = None,
    items_count: Optional[int] = None,
    error_category: Optional[str] = None,
    is_internal: bool = False
) -> None:
    """
    Records a live API telemetry event to SQLite.
    Fails safely without raising exceptions or disrupting API requests.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO monitoring_events (
                    timestamp, endpoint, method, status_code, duration_ms,
                    event_type, genre_filter, user_id, model_type,
                    assistant_mode, items_count, error_category, is_internal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                now_iso,
                endpoint,
                method,
                int(status_code),
                float(duration_ms),
                event_type,
                genre_filter,
                str(user_id) if user_id is not None else None,
                model_type,
                assistant_mode,
                int(items_count) if items_count is not None else None,
                error_category,
                1 if is_internal else 0
            ))
            conn.commit()
    except Exception as e:
        logger.warning("Failed to record monitoring event: %s", e)


def get_user_preferences_analytics(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes user taste history, most-liked genres, favorite actors, and favorite directors
    from real SQLite likes and favorites joined with the master catalog.
    """
    try:
        from src.catalog_service import get_master_movie_by_id

        with get_db_connection() as conn:
            cursor = conn.cursor()
            if user_id and str(user_id).strip():
                cursor.execute("SELECT movie_id FROM likes WHERE user_id = ? AND liked = 1;", (str(user_id),))
                like_mids = [r["movie_id"] for r in cursor.fetchall()]
                cursor.execute("SELECT movie_id, genres FROM favorites WHERE user_id = ?;", (str(user_id),))
                fav_rows = [dict(r) for r in cursor.fetchall()]
            else:
                cursor.execute("SELECT movie_id FROM likes WHERE liked = 1;")
                like_mids = [r["movie_id"] for r in cursor.fetchall()]
                cursor.execute("SELECT movie_id, genres FROM favorites;")
                fav_rows = [dict(r) for r in cursor.fetchall()]

        genre_counts: Dict[str, int] = {}
        actor_counts: Dict[str, int] = {}
        director_counts: Dict[str, int] = {}
        industry_counts: Dict[str, int] = {}

        # Aggregate from likes
        for mid in like_mids:
            m = get_master_movie_by_id(str(mid))
            if m:
                # Genres
                g_str = str(m.get("genre") or "")
                for g in re.split(r"[,|]+", g_str):
                    cg = g.strip()
                    if cg and cg.lower() not in ["none", "cinema"]:
                        genre_counts[cg] = genre_counts.get(cg, 0) + 1
                # Industry
                ind = str(m.get("industry") or "").strip()
                if ind:
                    industry_counts[ind] = industry_counts.get(ind, 0) + 1
                # Actors (top 3)
                c_str = str(m.get("cast") or "")
                for a in [act.strip() for act in c_str.split(",")[:3]]:
                    if a and len(a) > 2:
                        actor_counts[a] = actor_counts.get(a, 0) + 1
                # Director
                d_str = str(m.get("director") or "").strip()
                if d_str and len(d_str) > 2:
                    director_counts[d_str] = director_counts.get(d_str, 0) + 1

        # Aggregate from favorites (watchlist)
        for f in fav_rows:
            m = get_master_movie_by_id(str(f.get("movie_id", "")))
            g_str = str(f.get("genres") or (m.get("genre") if m else ""))
            for g in re.split(r"[,|]+", g_str):
                cg = g.strip()
                if cg and cg.lower() not in ["none", "cinema"]:
                    genre_counts[cg] = genre_counts.get(cg, 0) + 1
            if m:
                c_str = str(m.get("cast") or "")
                for a in [act.strip() for act in c_str.split(",")[:3]]:
                    if a and len(a) > 2:
                        actor_counts[a] = actor_counts.get(a, 0) + 1
                d_str = str(m.get("director") or "").strip()
                if d_str and len(d_str) > 2:
                    director_counts[d_str] = director_counts.get(d_str, 0) + 1

        total_genre_hits = sum(genre_counts.values()) or 1
        sorted_genres = [
            {"genre": g, "count": cnt, "percentage": round((cnt / total_genre_hits) * 100, 1)}
            for g, cnt in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        sorted_actors = [
            {"actor": a, "count": cnt}
            for a, cnt in sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        ]
        sorted_directors = [
            {"director": d, "count": cnt}
            for d, cnt in sorted(director_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        ]
        sorted_industries = [
            {"industry": ind, "count": cnt}
            for ind, cnt in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        ]

        primary_leaning = sorted_genres[0]["genre"] if sorted_genres else "Balanced"

        return {
            "total_likes": len(like_mids),
            "total_favorites": len(fav_rows),
            "primary_genre_leaning": primary_leaning,
            "top_liked_genres": sorted_genres,
            "top_liked_actors": sorted_actors,
            "top_liked_directors": sorted_directors,
            "top_industries": sorted_industries,
        }
    except Exception as e:
        logger.warning("Error computing user preference analytics: %s", e)
        return {
            "total_likes": 0,
            "total_favorites": 0,
            "primary_genre_leaning": "Balanced",
            "top_liked_genres": [],
            "top_liked_actors": [],
            "top_liked_directors": [],
            "top_industries": [],
        }


def get_monitoring_summary(exclude_internal: bool = True) -> Dict[str, Any]:
    """
    Computes real-time aggregated metrics from the monitoring_events table.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            where_clause = "WHERE is_internal = 0" if exclude_internal else "WHERE 1=1"

            # 1. Total Requests, Status Codes, and Latencies
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_requests,
                    AVG(duration_ms) as avg_latency_ms,
                    MIN(duration_ms) as min_latency_ms,
                    MAX(duration_ms) as max_latency_ms,
                    SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
                    SUM(CASE WHEN duration_ms > 500 THEN 1 ELSE 0 END) as slow_requests_count
                FROM monitoring_events
                {where_clause};
            """)
            summary_row = cursor.fetchone()

            total_requests = summary_row["total_requests"] or 0
            avg_latency = summary_row["avg_latency_ms"] or 0.0
            min_latency = summary_row["min_latency_ms"] or 0.0
            max_latency = summary_row["max_latency_ms"] or 0.0
            success_count = summary_row["success_count"] or 0
            error_count = summary_row["error_count"] or 0
            slow_requests = summary_row["slow_requests_count"] or 0

            # 2. Percentile Latencies (Median / P50, P95)
            cursor.execute(f"""
                SELECT duration_ms FROM monitoring_events
                {where_clause}
                ORDER BY duration_ms ASC;
            """)
            durations = [row["duration_ms"] for row in cursor.fetchall()]

            median_latency = 0.0
            p95_latency = 0.0
            has_sufficient_p95 = len(durations) >= 10

            if durations:
                n = len(durations)
                median_latency = durations[n // 2]
                p95_idx = int(0.95 * n)
                p95_latency = durations[min(p95_idx, n - 1)]

            # 3. Requests by Endpoint
            cursor.execute(f"""
                SELECT endpoint, COUNT(*) as count, AVG(duration_ms) as avg_ms
                FROM monitoring_events
                {where_clause}
                GROUP BY endpoint
                ORDER BY count DESC
                LIMIT 10;
            """)
            endpoint_stats = [dict(row) for row in cursor.fetchall()]

            # 4. HTTP Status Code Distribution
            cursor.execute(f"""
                SELECT status_code, COUNT(*) as count
                FROM monitoring_events
                {where_clause}
                GROUP BY status_code
                ORDER BY count DESC;
            """)
            status_stats = [dict(row) for row in cursor.fetchall()]

            # 5. Recommendation Metrics
            cursor.execute("""
                SELECT
                    COUNT(*) as rec_requests,
                    AVG(duration_ms) as avg_rec_ms,
                    SUM(CASE WHEN items_count = 0 THEN 1 ELSE 0 END) as empty_results_count
                FROM monitoring_events
                WHERE event_type = 'recommendation';
            """)
            rec_row = cursor.fetchone()
            rec_requests = rec_row["rec_requests"] or 0
            avg_rec_ms = rec_row["avg_rec_ms"] or 0.0
            empty_rec_count = rec_row["empty_results_count"] or 0
            empty_rate = (empty_rec_count / rec_requests * 100.0) if rec_requests > 0 else 0.0

            # Top requested genres
            cursor.execute("""
                SELECT genre_filter, COUNT(*) as count
                FROM monitoring_events
                WHERE genre_filter IS NOT NULL AND genre_filter != ''
                GROUP BY genre_filter
                ORDER BY count DESC
                LIMIT 8;
            """)
            top_genres = [dict(row) for row in cursor.fetchall()]

            # Model type usage
            cursor.execute("""
                SELECT model_type, COUNT(*) as count
                FROM monitoring_events
                WHERE model_type IS NOT NULL
                GROUP BY model_type
                ORDER BY count DESC;
            """)
            model_usage = [dict(row) for row in cursor.fetchall()]

            # 6. AI Assistant Metrics
            cursor.execute("""
                SELECT
                    COUNT(*) as total_assistant_queries,
                    SUM(CASE WHEN assistant_mode = 'gemini_flash' THEN 1 ELSE 0 END) as gemini_success_count,
                    SUM(CASE WHEN assistant_mode = 'catalog_fallback' THEN 1 ELSE 0 END) as fallback_count,
                    AVG(duration_ms) as avg_assistant_ms
                FROM monitoring_events
                WHERE event_type = 'assistant';
            """)
            ast_row = cursor.fetchone()
            total_assistant = ast_row["total_assistant_queries"] or 0
            gemini_success = ast_row["gemini_success_count"] or 0
            fallback_count = ast_row["fallback_count"] or 0
            avg_assistant_ms = ast_row["avg_assistant_ms"] or 0.0

            # Assistant upstream errors
            cursor.execute("""
                SELECT error_category, COUNT(*) as count
                FROM monitoring_events
                WHERE event_type = 'assistant' AND error_category IS NOT NULL
                GROUP BY error_category
                ORDER BY count DESC;
            """)
            assistant_errors = [dict(row) for row in cursor.fetchall()]

            # 7. Time-series bucketed requests (hourly / minute)
            cursor.execute(f"""
                SELECT substr(timestamp, 1, 16) as time_bucket, COUNT(*) as count, AVG(duration_ms) as avg_latency
                FROM monitoring_events
                {where_clause}
                GROUP BY time_bucket
                ORDER BY time_bucket ASC
                LIMIT 50;
            """)
            time_series = [dict(row) for row in cursor.fetchall()]

            # 8. Real-time User Interaction Counts
            cursor.execute("SELECT COUNT(*) FROM likes WHERE liked = 1;")
            total_db_likes = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM favorites;")
            total_db_favs = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM view_history;")
            total_db_views = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM search_history;")
            total_db_searches = cursor.fetchone()[0] or 0

            # 9. User Taste History & Analytics
            pref_stats = get_user_preferences_analytics()

            return {
                "total_requests": total_requests,
                "success_count": success_count,
                "error_count": error_count,
                "slow_requests": slow_requests,
                "avg_latency_ms": round(avg_latency, 2),
                "min_latency_ms": round(min_latency, 2),
                "max_latency_ms": round(max_latency, 2),
                "median_latency_ms": round(median_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "has_sufficient_p95": has_sufficient_p95,
                "sample_size": len(durations),
                "endpoint_stats": endpoint_stats,
                "status_stats": status_stats,
                "time_series": time_series,
                "user_interactions": {
                    "likes": total_db_likes,
                    "favorites": total_db_favs,
                    "views": total_db_views,
                    "searches": total_db_searches
                },
                "user_preference_stats": pref_stats,
                "recommendation_metrics": {
                    "total_requests": rec_requests,
                    "avg_latency_ms": round(avg_rec_ms, 2),
                    "empty_results_count": empty_rec_count,
                    "empty_result_rate_pct": round(empty_rate, 2),
                    "top_requested_genres": top_genres,
                    "model_usage": model_usage
                },
                "assistant_metrics": {
                    "total_queries": total_assistant,
                    "gemini_success_count": gemini_success,
                    "fallback_count": fallback_count,
                    "avg_latency_ms": round(avg_assistant_ms, 2),
                    "errors": assistant_errors
                }
            }
    except Exception as e:
        logger.error("Error generating monitoring summary: %s", e)
        return {
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "slow_requests": 0,
            "avg_latency_ms": 0.0,
            "min_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "median_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "has_sufficient_p95": False,
            "sample_size": 0,
            "endpoint_stats": [],
            "status_stats": [],
            "time_series": [],
            "recommendation_metrics": {
                "total_requests": 0,
                "avg_latency_ms": 0.0,
                "empty_results_count": 0,
                "empty_result_rate_pct": 0.0,
                "top_requested_genres": [],
                "model_usage": []
            },
            "assistant_metrics": {
                "total_queries": 0,
                "gemini_success_count": 0,
                "fallback_count": 0,
                "avg_latency_ms": 0.0,
                "errors": []
            }
        }


def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns the most recent monitoring telemetry events."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, endpoint, method, status_code, duration_ms,
                       event_type, genre_filter, user_id, model_type, assistant_mode,
                       items_count, error_category, is_internal
                FROM monitoring_events
                ORDER BY id DESC
                LIMIT ?;
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error("Error fetching recent events: %s", e)
        return []


def prune_events(keep_latest: int = 10000) -> int:
    """
    Maintains bounded retention by deleting older events beyond keep_latest.
    Returns the number of rows deleted.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM monitoring_events
                WHERE id NOT IN (
                    SELECT id FROM monitoring_events ORDER BY id DESC LIMIT ?
                );
            """, (keep_latest,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
    except Exception as e:
        logger.error("Error pruning events: %s", e)
        return 0


def clear_all_monitoring_and_interaction_data() -> Dict[str, int]:
    """
    Permanently clears all telemetry events, user likes, favorites, search history,
    and viewing history while safely preserving table schemas and user accounts.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM monitoring_events;")
            events_cleared = cursor.rowcount
            cursor.execute("DELETE FROM likes;")
            likes_cleared = cursor.rowcount
            cursor.execute("DELETE FROM favorites;")
            favs_cleared = cursor.rowcount
            cursor.execute("DELETE FROM search_history;")
            searches_cleared = cursor.rowcount
            cursor.execute("DELETE FROM view_history;")
            views_cleared = cursor.rowcount
            conn.commit()

            logger.info(
                "Cleared all monitoring and user interaction data: %d events, %d likes, %d favs, %d searches, %d views.",
                events_cleared, likes_cleared, favs_cleared, searches_cleared, views_cleared
            )
            return {
                "events_cleared": events_cleared,
                "likes_cleared": likes_cleared,
                "favorites_cleared": favs_cleared,
                "searches_cleared": searches_cleared,
                "views_cleared": views_cleared
            }
    except Exception as e:
        logger.error("Error clearing monitoring data: %s", e)
        return {}
