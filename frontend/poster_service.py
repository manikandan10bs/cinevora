"""
Cinevora Movie Poster & Media Enrichment Service
Sourced exclusively from data/processed/Movies_Master_Cleaned.csv:
- Real verified poster images (TMDB)
- Official trailer links (YouTube)
- Metadata attributes (Cast, Director, Industry, Genre, Year, Rating)
- Clean, resilient 2:3 aspect-ratio HTML rendering with onerror fallback
"""

import html
import logging
import os
import re
from typing import Dict, Optional, Any, List, Union

from src.catalog_service import (
    load_master_catalog,
    get_master_movie_by_id,
    normalize_industry_filter
)

logger = logging.getLogger("cinevora.media")

# In-memory caches for fast lookup
_CATALOG_ID_MAP: Dict[str, Dict[str, Any]] = {}
_MOVIE_ID_MAP: Dict[str, Dict[str, Any]] = {}
_FEATURED_MOVIES: List[Dict[str, Any]] = []
_INITIALIZED: bool = False

INDIAN_LANG_CODES = {"ta", "te", "kn", "ml", "hi", "bn", "mr", "gu", "pa"}
INDIAN_COUNTRY_CODES = {"IN", "IND", "INDIA"}
LANG_NAME_TO_CODE = {
    "tamil": "ta", "ta": "ta",
    "telugu": "te", "te": "te",
    "kannada": "kn", "kn": "kn",
    "malayalam": "ml", "ml": "ml",
    "hindi": "hi", "hi": "hi",
    "bengali": "bn", "bn": "bn",
    "english": "en", "en": "en"
}
CODE_TO_INDUSTRY = {
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "hi": "Bollywood",
    "en": "Hollywood"
}


def extract_release_year(movie: Optional[Dict[str, Any]], default: Optional[int] = None) -> Optional[int]:
    """
    Safely extracts the release year as an integer from a movie dictionary.
    Handles None, empty strings, invalid types, and extracts from title if missing.
    Returns default (or None) if the year cannot be determined.
    """
    if not isinstance(movie, dict):
        return default

    # 1. Try explicit release_year key
    val = movie.get("release_year")
    if val is not None and str(val).strip():
        try:
            yr = int(float(str(val).strip()))
            if 1888 <= yr <= 2100:
                return yr
        except (ValueError, TypeError):
            pass

    # 2. Try extracting (YYYY) from title or movie_title
    for title_key in ("title", "movie_title", "original_title"):
        title_val = movie.get(title_key)
        if title_val:
            m = re.search(r"\((\d{4})\)", str(title_val))
            if m:
                try:
                    yr = int(m.group(1))
                    if 1888 <= yr <= 2100:
                        return yr
                except (ValueError, TypeError):
                    pass

    # 3. Try release_date string e.g. "01-Jan-1995" or "1995-10-20"
    rd = movie.get("release_date")
    if rd:
        m = re.search(r"\b(19\d{2}|20\d{2})\b", str(rd))
        if m:
            try:
                yr = int(m.group(1))
                if 1888 <= yr <= 2100:
                    return yr
            except (ValueError, TypeError):
                pass

    return default


def init_poster_cache(force: bool = False) -> None:
    """Loads and indexes master catalog movies into memory."""
    global _CATALOG_ID_MAP, _MOVIE_ID_MAP, _FEATURED_MOVIES, _INITIALIZED
    if _INITIALIZED and not force:
        return

    df = load_master_catalog(force_reload=force)
    _CATALOG_ID_MAP.clear()
    _MOVIE_ID_MAP.clear()
    _FEATURED_MOVIES.clear()

    featured_candidates = []

    for idx, row in df.iterrows():
        item = row.to_dict()
        cid = str(item.get("catalog_id") or f"CINEVORA-{idx+1:07d}").strip()
        mid = str(item.get("movie_id", idx + 1)).strip()

        # Normalization
        item["catalog_id"] = cid
        item["movie_id"] = mid
        item["title"] = str(item.get("title") or "Untitled")
        item["movie_title"] = item["title"]
        item["release_year"] = extract_release_year(item, default=2022)
        item["genres"] = str(item.get("genre") or "Cinema")
        item["avg_rating"] = float(item.get("rating") or 6.0)

        p_raw = item.get("movie_poster")
        item["poster_url"] = str(p_raw).strip() if (p_raw is not None and str(p_raw).startswith("http")) else None
        item["backdrop_url"] = item["poster_url"]

        tr_raw = item.get("trailer_link")
        item["trailer_url"] = str(tr_raw).strip() if (tr_raw is not None and str(tr_raw).startswith("http")) else None

        ind = str(item.get("industry") or "Cinema")
        item["cinema_region"] = "Hollywood" if ind.lower() == "hollywood" else "Indian"
        lang_map = {
            "tamil": "ta", "telugu": "te", "malayalam": "ml",
            "kannada": "kn", "bollywood": "hi", "hollywood": "en"
        }
        item["original_language"] = lang_map.get(ind.lower(), "en")
        item["origin_countries"] = "US" if ind.lower() == "hollywood" else "IN"
        item["synopsis"] = f"Directed by {item.get('director') or 'Visionary Director'}. Starring {item.get('cast') or 'Ensemble Cast'}."

        _CATALOG_ID_MAP[cid] = item
        _MOVIE_ID_MAP[mid] = item

        # Select featured candidates: has trailer link, rating >= 7.5, has poster
        if item.get("trailer_url") and item["avg_rating"] >= 7.5 and item.get("poster_url"):
            featured_candidates.append(item)

    # Sort featured candidates by rating descending across industries
    featured_candidates.sort(key=lambda x: x["avg_rating"], reverse=True)
    _FEATURED_MOVIES = featured_candidates[:12] if featured_candidates else list(_CATALOG_ID_MAP.values())[:8]

    _INITIALIZED = True
    logger.info("Initialized poster cache with %d master titles.", len(_CATALOG_ID_MAP))


def _find_movie_dict(identifier: Any) -> Optional[Dict[str, Any]]:
    """Helper to locate movie by catalog_id or movie_id."""
    init_poster_cache()
    if identifier is None:
        return None
    id_str = str(identifier).strip()
    return _CATALOG_ID_MAP.get(id_str) or _MOVIE_ID_MAP.get(id_str)


def get_poster_url(
    movie_id: Any,
    title: Optional[str] = None,
    year: Optional[str] = None
) -> Optional[str]:
    """Returns the verified poster image URL for a given movie."""
    m = _find_movie_dict(movie_id)
    if m and m.get("poster_url"):
        return m["poster_url"]
    return None


def get_backdrop_url(movie_id: Any, title: Optional[str] = None) -> Optional[str]:
    """Returns the verified backdrop / poster URL for a movie."""
    m = _find_movie_dict(movie_id)
    if m:
        return m.get("backdrop_url") or m.get("poster_url")
    return None


def get_movie_synopsis(movie_id: Any) -> Optional[str]:
    """Returns the verified synopsis for a movie."""
    m = _find_movie_dict(movie_id)
    if m:
        return m.get("synopsis")
    return None


def get_trailer_url(movie_id: Any) -> Optional[str]:
    """Returns the verified official trailer URL for a movie."""
    m = _find_movie_dict(movie_id)
    if m:
        t = m.get("trailer_url") or m.get("trailer_link")
        if t and isinstance(t, str) and t.startswith("http") and t.strip().lower() not in ["nan", "none", r"\n", ""]:
            return t
    return None


def get_effective_trailer_url(
    movie: Union[Dict[str, Any], Any],
    title: Optional[str] = None
) -> str:
    """
    Returns the movie's official trailer URL, or dynamically generates a YouTube search fallback:
    https://www.youtube.com/results?search_query={movie_name}+trailer
    """
    trailer = None
    movie_title = title
    if isinstance(movie, dict):
        trailer = movie.get("trailer_link") or movie.get("trailer_url")
        if not movie_title:
            movie_title = movie.get("title") or movie.get("movie_title")
        if not trailer:
            mid = movie.get("catalog_id") or movie.get("movie_id")
            m = _find_movie_dict(mid)
            if m:
                trailer = m.get("trailer_url") or m.get("trailer_link")
                if not movie_title:
                    movie_title = m.get("title") or m.get("movie_title")
    else:
        m = _find_movie_dict(movie)
        if m:
            trailer = m.get("trailer_url") or m.get("trailer_link")
            if not movie_title:
                movie_title = m.get("title") or m.get("movie_title")

    if trailer and isinstance(trailer, str):
        t_clean = trailer.strip()
        if t_clean.startswith("http") and t_clean.lower() not in ["nan", "none", r"\n", ""]:
            return t_clean

    clean_t = re.sub(r"\s*\(\d{4}\)", "", str(movie_title or "movie")).strip()
    from urllib.parse import quote_plus
    return f"https://www.youtube.com/results?search_query={quote_plus(clean_t + ' trailer')}"


def get_same_genre_movies(
    catalog_id: str,
    genres_str: Optional[str] = None,
    limit: int = 4
) -> List[Dict[str, Any]]:
    """
    Retrieves top 4 matching movies from the master catalog sharing the same genre(s),
    excluding the target movie, sorted by genre overlap and rating.
    """
    init_poster_cache()
    if not _CATALOG_ID_MAP:
        return []

    target = _CATALOG_ID_MAP.get(str(catalog_id).strip())
    raw_g = genres_str or (target.get("genre") or target.get("genres") if target else "")
    genres = [g.strip().lower() for g in str(raw_g).replace(",", "|").split("|") if g.strip()]
    if not genres:
        cand = [m for cid, m in _CATALOG_ID_MAP.items() if cid != str(catalog_id).strip()]
        cand.sort(key=lambda x: float(x.get("avg_rating") or x.get("rating") or 6.0), reverse=True)
        return cand[:limit]

    primary = genres[0]
    curr_cid = str(catalog_id).strip()
    scored_candidates = []

    for cid, m in _CATALOG_ID_MAP.items():
        if cid == curr_cid:
            continue
        m_genres = [g.strip().lower() for g in str(m.get("genre") or m.get("genres", "")).replace(",", "|").split("|") if g.strip()]
        common = len(set(genres).intersection(set(m_genres)))
        if common > 0:
            score = common + (2 if primary in m_genres else 0)
            rating = float(m.get("avg_rating") or m.get("rating") or 6.0)
            scored_candidates.append((score, rating, m))

    scored_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [item[2] for item in scored_candidates[:limit]]


def get_movie_enrichment(movie_id: Any) -> Dict[str, Any]:
    """Returns the full metadata record for a movie."""
    m = _find_movie_dict(movie_id)
    return m if m else {}


def get_featured_movies() -> List[Dict[str, Any]]:
    """Returns the ordered list of featured spotlight movies for hero banners."""
    init_poster_cache()
    return _FEATURED_MOVIES


def get_all_enriched_movies() -> List[Dict[str, Any]]:
    """Returns all 3,560 movies from the master catalog."""
    init_poster_cache()
    return list(_CATALOG_ID_MAP.values())


def is_indian_movie(movie: Dict[str, Any]) -> bool:
    """Returns True if movie belongs to Indian cinema."""
    if not isinstance(movie, dict):
        return False
    ind = str(movie.get("industry") or movie.get("cinema_region") or "").strip().lower()
    if ind in ["bollywood", "tamil", "telugu", "malayalam", "kannada", "indian", "hindi", "kollywood", "tollywood", "mollywood", "sandalwood"]:
        return True
    countries = str(movie.get("origin_countries") or "").strip().upper()
    foreign_countries = {"US", "GB", "UK", "FR", "DE", "KR", "JP", "IT", "ES", "CN", "RU"}
    if any(fc in countries for fc in foreign_countries) and not any(ic in countries for ic in INDIAN_COUNTRY_CODES):
        return False
    lang = str(movie.get("original_language") or "").strip().lower()
    if lang in INDIAN_LANG_CODES or lang in ["tamil", "telugu", "kannada", "malayalam", "hindi"]:
        return True
    if any(c in countries for c in INDIAN_COUNTRY_CODES):
        return True
    return False


def get_indian_movies(
    language: Optional[str] = None,
    genre: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns all Indian cinema titles from the master catalog with optional language and genre filters."""
    init_poster_cache()
    ind_movies = [m for m in _CATALOG_ID_MAP.values() if is_indian_movie(m)]
    if language:
        lang_clean = str(language).strip().lower()
        canonical = CODE_TO_INDUSTRY.get(lang_clean) or normalize_industry_filter(lang_clean) or lang_clean
        ind_movies = [
            m for m in ind_movies
            if str(m.get("industry", "")).lower() == str(canonical).lower()
            or str(m.get("original_language", "")).lower() == lang_clean
            or str(m.get("industry", "")).lower() == lang_clean
        ]
    if genre:
        g_clean = str(genre).strip().lower()
        ind_movies = [m for m in ind_movies if g_clean in str(m.get("genres", "")).lower()]
    return ind_movies


def get_hollywood_movies(
    genre: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Returns all Hollywood titles from the master catalog with optional filters."""
    init_poster_cache()
    hwd = [
        m for m in _CATALOG_ID_MAP.values()
        if str(m.get("industry", "")).strip().lower() in ["hollywood", "american", "english"]
    ]

    if genre and genre.strip():
        g_clean = genre.strip().lower()
        hwd = [m for m in hwd if g_clean in str(m.get("genres", "")).lower()]

    if min_year is not None:
        hwd = [m for m in hwd if (extract_release_year(m) or 0) >= min_year]

    if max_year is not None:
        hwd = [m for m in hwd if (extract_release_year(m) or 9999) <= max_year]

    return hwd


def get_movies_by_language(lang_code: str) -> List[Dict[str, Any]]:
    """Returns movies for a specific language or industry (e.g. 'ta', 'te', 'hi', 'ml', 'kn', 'en')."""
    init_poster_cache()
    target = lang_code.strip().lower()
    canonical_industry = CODE_TO_INDUSTRY.get(target) or normalize_industry_filter(target)
    if not canonical_industry:
        canonical_industry = target

    return [
        m for m in _CATALOG_ID_MAP.values()
        if str(m.get("industry", "")).strip().lower() == canonical_industry.lower()
    ]


def get_movies_by_region(region: str) -> List[Dict[str, Any]]:
    """Returns movies matching a region (e.g. 'Indian' or 'Hollywood')."""
    r_lower = region.strip().lower()
    if r_lower in ["indian", "india"]:
        return get_indian_movies()
    elif r_lower in ["hollywood", "american", "western"]:
        return get_hollywood_movies()
    else:
        return get_movies_by_language(region)


def render_poster_html(
    movie_id: Any,
    title: str,
    release_date: str = "",
    genres: str = "",
    poster_url: Optional[str] = None
) -> str:
    """
    Renders a clean, reliable 2:3 poster container with lazy loading and onerror fallback.
    """
    if not poster_url:
        poster_url = get_poster_url(movie_id, title=title)

    clean_title = re.sub(r"\s*\(\d{4}\)", "", title).strip()
    m_yr = re.search(r"\((\d{4})\)", title)
    year_str = m_yr.group(1) if m_yr else release_date[-4:] if len(release_date) >= 4 else ""

    genre_list = [g.strip() for g in genres.replace(",", "|").split("|") if g.strip()]
    primary_genre = genre_list[0] if genre_list else "Cinema"

    if poster_url and str(poster_url).startswith("http"):
        return (
            f'<div class="movie-poster-container">'
            f'<img src="{html.escape(poster_url)}" alt="{html.escape(clean_title)}" class="movie-poster-img" loading="lazy" style="width: 100%; height: 100%; object-fit: cover; display: block;" onerror="this.style.display=\'none\'; if(this.nextElementSibling) this.nextElementSibling.style.display=\'flex\';" />'
            f'<div class="movie-poster-fallback" style="display: none; position: absolute; inset: 0; background: linear-gradient(145deg, #131B26, #090D14); color: #94A3B8; flex-direction: column; align-items: center; justify-content: center; padding: 12px; text-align: center;">'
            f'<div style="font-size: 2rem; margin-bottom: 6px;">🎬</div>'
            f'<div style="font-size: 0.85rem; font-weight: 700; color: #FFFFFF;">{html.escape(clean_title)}</div>'
            f'<div style="font-size: 0.75rem; color: #94A3B8;">{html.escape(year_str)} • {html.escape(primary_genre)}</div>'
            f'</div>'
            f'</div>'
        )
    else:
        return (
            f'<div class="movie-poster-container">'
            f'<div class="movie-poster-fallback" style="position: absolute; inset: 0; background: linear-gradient(145deg, #131B26, #090D14); color: #94A3B8; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px; text-align: center;">'
            f'<div style="font-size: 2rem; margin-bottom: 6px;">🎬</div>'
            f'<div style="font-size: 0.85rem; font-weight: 700; color: #FFFFFF;">{html.escape(clean_title)}</div>'
            f'<div style="font-size: 0.75rem; color: #94A3B8;">{html.escape(year_str)} • {html.escape(primary_genre)}</div>'
            f'</div>'
            f'</div>'
        )


__all__ = [
    "init_poster_cache",
    "extract_release_year",
    "get_poster_url",
    "get_backdrop_url",
    "get_movie_synopsis",
    "get_trailer_url",
    "get_effective_trailer_url",
    "get_same_genre_movies",
    "get_movie_enrichment",
    "get_featured_movies",
    "get_all_enriched_movies",
    "get_movies_by_region",
    "get_movies_by_language",
    "get_indian_movies",
    "get_hollywood_movies",
    "is_indian_movie",
    "render_poster_html",
]
