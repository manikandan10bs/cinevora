"""
Cinevora Suggested Movies Engine & Presentation Panel (Cinematic Dark Edition)
Dynamically computes and displays movie suggestions based on:
1. Recently searched titles and genres (e.g. searching 'action' or 'comedy')
2. Liked movies (retrieved from SQLite and session state)
3. Combined multi-genre taste signals (e.g. liking Action and searching Comedy
   yields suggestions spanning both Action and Comedy, prioritizing crossovers).
4. Fallback for cold-start users (top-rated popular blockbusters).
"""

from typing import Dict, List, Set, Any, Optional
import streamlit as st

from frontend.api_client import api_client
from frontend.config import ALL_GENRES
from frontend.components import render_movie_card, render_empty_state
try:
    from frontend.poster_service import get_all_enriched_movies
except ImportError:
    from poster_service import get_all_enriched_movies  # type: ignore


# -----------------------------------------------------------------------------
# Interaction Tracking & Persistence
# -----------------------------------------------------------------------------
def record_search(
    query: str,
    results: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[str] = None
):
    """
    Records a search query and extracts implied genre signals.
    Inspects both query tokens (e.g. 'action', 'comedy') and returned movie genres.
    Persists query to SQLite when user_id is provided.
    """
    if not query or not query.strip():
        return

    q_clean = query.strip()

    # 1. Maintain recent search queries list
    recent_queries: List[str] = st.session_state.setdefault("recent_search_queries", [])
    if q_clean not in recent_queries:
        recent_queries.insert(0, q_clean)
    if len(recent_queries) > 10:
        recent_queries.pop()

    # 2. Detect genres directly from query text
    detected_from_text: Set[str] = set()
    q_lower = q_clean.lower()
    for g in ALL_GENRES:
        if g.lower() in q_lower:
            detected_from_text.add(g)

    # 3. Detect dominant genres from matching search results
    detected_from_results: Set[str] = set()
    matched_movie_id: Optional[int] = None
    matched_movie_title: Optional[str] = None

    if results:
        first_movie = results[0]
        matched_movie_id = first_movie.get("movie_id")
        matched_movie_title = first_movie.get("movie_title")

        for m in results[:5]:
            genres_str = m.get("genres", "")
            for g in ALL_GENRES:
                if g in genres_str:
                    detected_from_results.add(g)

    # 4. Save to session state
    searched_genres: Set[str] = st.session_state.setdefault("recent_search_genres", set())
    searched_genres.update(detected_from_text)
    if detected_from_results and not detected_from_text:
        # If query wasn't a genre word itself (e.g. 'Terminator'), add top result genres
        searched_genres.update(detected_from_results)

    # 5. Persist to SQLite if user_id is provided
    if user_id:
        active_matched = detected_from_text or detected_from_results
        genres_repr = "|".join(sorted(list(active_matched))) if active_matched else None
        try:
            api_client.record_search_history(
                user_id=user_id,
                query=q_clean,
                matched_genres=genres_repr,
                matched_movie_id=matched_movie_id,
                matched_movie_title=matched_movie_title
            )
        except Exception:
            pass


def record_genre_filter(genre: str):
    """Records an explicit genre filter selection from Discover or Home."""
    if not genre or genre == "All Genres":
        return
    searched_genres: Set[str] = st.session_state.setdefault("recent_search_genres", set())
    searched_genres.add(genre)


def clear_search_signals(user_id: Optional[str] = None):
    """Clears recent search queries and searched genres."""
    st.session_state["recent_search_queries"] = []
    st.session_state["recent_search_genres"] = set()
    if user_id:
        try:
            api_client.clear_search_history(user_id)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Active Taste Aggregation
# -----------------------------------------------------------------------------
def get_active_taste_profile(user_id: str) -> Dict[str, Any]:
    """
    Aggregates active taste signals from liked movies and recent searches.
    Returns:
        {
            "liked_genres": {"Action", ...},
            "searched_genres": {"Comedy", ...},
            "combined_genres": ["Action", "Comedy"],
            "breakdown": {"Action": ["❤️ Liked"], "Comedy": ["🔍 Searched"]},
            "liked_ids": {50, ...}
        }
    """
    liked_genres: Set[str] = set()
    breakdown: Dict[str, List[str]] = {}

    # 1. Inspect liked movies from cache or backend
    likes_cache_key = f"likes_set_{user_id}"
    liked_ids: Set[int] = st.session_state.get(likes_cache_key, set())
    if not liked_ids:
        liked_ids = set(api_client.get_likes(user_id))
        st.session_state[likes_cache_key] = liked_ids

    meta_cache = st.session_state.setdefault("liked_meta_cache", {})

    for movie_id in list(liked_ids):
        genres_str = ""
        if movie_id in meta_cache:
            genres_str = meta_cache[movie_id].get("genres", "")
        else:
            # Fetch once from backend if not yet cached
            details = api_client.get_movie_details(movie_id)
            if details:
                genres_str = details.get("genres", "")
                meta_cache[movie_id] = {
                    "movie_id": movie_id,
                    "movie_title": details.get("movie_title", ""),
                    "genres": genres_str
                }
        if genres_str:
            for g in ALL_GENRES:
                if g in genres_str:
                    liked_genres.add(g)
                    breakdown.setdefault(g, []).append("❤️ Liked")

    # 2. Inspect recently searched genres (restore from SQLite if session is empty)
    searched_genres: Set[str] = st.session_state.setdefault("recent_search_genres", set())
    if not searched_genres and user_id:
        try:
            history_records = api_client.get_search_history(user_id, limit=10)
            for rec in history_records:
                mg = rec.get("matched_genres")
                if mg:
                    for g in mg.split("|"):
                        if g in ALL_GENRES:
                            searched_genres.add(g)
        except Exception:
            pass

    for g in searched_genres:
        breakdown.setdefault(g, []).append("🔍 Searched")

    combined = sorted(list(liked_genres.union(searched_genres)))

    return {
        "liked_genres": liked_genres,
        "searched_genres": searched_genres,
        "combined_genres": combined,
        "breakdown": breakdown,
        "liked_ids": liked_ids
    }


# -----------------------------------------------------------------------------
# Suggested Movies Retrieval
# -----------------------------------------------------------------------------
def get_suggested_movies(user_id: str, limit: int = 6) -> Dict[str, Any]:
    """
    Fetches movies matching the user's active taste profile.
    If the user likes Action and searched Comedy, fetches movies from Action and Comedy,
    prioritizing movies that span both, while excluding already-liked titles.
    If no history exists (cold-start), falls back to top-rated popular blockbusters.
    """
    profile = get_active_taste_profile(user_id)
    combined = profile["combined_genres"]
    liked_ids = set(profile.get("liked_ids", set()))
    try:
        remote_likes = api_client.get_likes(user_id)
        if remote_likes:
            liked_ids.update(remote_likes)
    except Exception:
        pass
    liked_ids_str = set(str(x).strip() for x in liked_ids)

    # Cold start scenario: no search or likes history
    if not combined:
        fallback_data = api_client.search_movies(
            sort_by="popularity",
            limit=limit + len(liked_ids) + 4
        )
        candidates = [
            m for m in fallback_data.get("results", [])
            if str(m.get("movie_id", "")).strip() not in liked_ids_str and
               str(m.get("catalog_id", "")).strip() not in liked_ids_str and
               m.get("movie_id") not in liked_ids
        ]
        suggested_list: List[Dict[str, Any]] = []
        for m in candidates[:limit]:
            m["suggestion_reason"] = "Popular Blockbuster"
            suggested_list.append(m)

        return {
            "movies": suggested_list,
            "profile": profile,
            "is_cold_start": True
        }

    # Query backend for movies matching any of the combined genres
    genre_param = ",".join(combined)
    search_data = api_client.search_movies(
        genre=genre_param,
        sort_by="popularity",
        limit=limit + len(liked_ids) + 8
    )

    all_matches = search_data.get("results", [])

    # Filter out already-liked movies to keep suggestions fresh
    filtered = [
        m for m in all_matches
        if str(m.get("movie_id", "")).strip() not in liked_ids_str and
           str(m.get("catalog_id", "")).strip() not in liked_ids_str and
           m.get("movie_id") not in liked_ids
    ]

    # Find cross-language matches from master catalog titles
    enriched_candidates = []
    seen_ids = set(str(m.get("movie_id", "")).strip() for m in filtered).union(
        str(m.get("catalog_id", "")).strip() for m in filtered
    ).union(liked_ids_str)

    for em in get_all_enriched_movies():
        em_cid = str(em.get("catalog_id", "")).strip()
        em_mid = str(em.get("movie_id", "")).strip()
        if em_cid in seen_ids or em_mid in seen_ids:
            continue
        em_genres = str(em.get("genres", ""))
        em_hits = [g for g in combined if g.lower() in em_genres.lower()]
        if em_hits:
            candidate = dict(em)
            candidate["movie_id"] = em_cid or em_mid
            candidate["movie_title"] = em.get("title") or em.get("movie_title")
            candidate["genres"] = em_genres
            candidate["predicted_rating"] = em.get("avg_rating", 6.5)
            region = em.get("cinema_region", "Cinema")
            candidate["suggestion_reason"] = f"Cross-Language: {region} {' + '.join(em_hits[:2])}"
            enriched_candidates.append(candidate)
            seen_ids.add(em_cid)
            seen_ids.add(em_mid)

    # Interleave enriched cross-language recommendations with catalog matches
    merged_candidates: List[Dict[str, Any]] = []
    e_idx = 0
    f_idx = 0
    while len(merged_candidates) < limit and (e_idx < len(enriched_candidates) or f_idx < len(filtered)):
        if e_idx < len(enriched_candidates):
            merged_candidates.append(enriched_candidates[e_idx])
            e_idx += 1
        if len(merged_candidates) < limit and f_idx < len(filtered):
            merged_candidates.append(filtered[f_idx])
            f_idx += 1

    # Annotate suggestions with explanation badges
    suggested_list: List[Dict[str, Any]] = []
    for m in merged_candidates[:limit]:
        if "suggestion_reason" not in m:
            m_genres = m.get("genres", "")
            hits = [g for g in combined if g in m_genres]
            if len(hits) >= 2:
                m["suggestion_reason"] = f"Matches your taste: {' + '.join(hits[:3])}!"
            elif len(hits) == 1:
                hit = hits[0]
                reasons = profile["breakdown"].get(hit, [])
                m["suggestion_reason"] = f"Based on your {', '.join(set(reasons))} ({hit})"
            else:
                m["suggestion_reason"] = "Recommended for your active taste"

        suggested_list.append(m)

    return {
        "movies": suggested_list,
        "profile": profile,
        "is_cold_start": False
    }


# -----------------------------------------------------------------------------
# Presentation Panel / Row
# -----------------------------------------------------------------------------
def render_suggested_movies_panel(user_id: str):
    """
    Renders the dedicated 'Recommended for You' section:
    - Displays dynamic recommendations based on recently searched and liked movies
    - Shows active signal badges (e.g. Liked: Action | Searched: Comedy)
    - Provides quick testing presets to demonstrate Action, Comedy, or Action+Comedy
    - Shows interactive movie cards with full details, save, and like controls.
    """
    data = get_suggested_movies(user_id=user_id, limit=6)
    movies = data.get("movies", [])
    profile = data.get("profile", {})
    combined_genres = profile.get("combined_genres", [])
    breakdown = profile.get("breakdown", {})
    is_cold_start = data.get("is_cold_start", False)

    st.markdown(
        """
        <div class="suggestion-panel">
            <div style="font-family: 'Cinzel', serif; font-size: 1.35rem; font-weight: 800; color: #FFFFFF; letter-spacing: 0.02em;">
                ✨ Recommended for You
            </div>
            <div style="color: #9CA3AF; font-size: 0.86rem; margin-top: 3px;">
                Dynamic personalized recommendations adapting instantly to your searches and liked movies
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Signals & Preset Testing Bar
    sig_col1, sig_col2 = st.columns([3.2, 1.8])

    with sig_col1:
        if combined_genres:
            badges_html = []
            for g in combined_genres:
                reasons = " & ".join(set(breakdown.get(g, ["Active"])))
                badges_html.append(
                    f'<span class="taste-badge"><b>{g}</b> ({reasons})</span>'
                )
            st.markdown(
                f'<div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 8px;">'
                f'<span style="color: #CBD5E1; font-size: 0.82rem; font-weight: 700;">Active Taste Signals:</span>'
                f'{"".join(badges_html)}'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="color: #9CA3AF; font-size: 0.84rem; margin-bottom: 6px;">'
                '💡 <i>New discovery profile: Showing trending blockbusters. Search a genre above or click Like to personalize!</i>'
                '</div>',
                unsafe_allow_html=True
            )

    with sig_col2:
        # Quick Taste Simulation Presets for easy user testing
        t1, t2, t3, t4 = st.columns([1, 1, 1.2, 0.8])
        with t1:
            if st.button("💥 Action", key=f"sim_action_{user_id}", help="Simulate search: Action", use_container_width=True):
                record_search("action", user_id=user_id)
                st.rerun()
        with t2:
            if st.button("😂 Comedy", key=f"sim_comedy_{user_id}", help="Simulate search: Comedy", use_container_width=True):
                record_search("comedy", user_id=user_id)
                st.rerun()
        with t3:
            if st.button("💥+😂 Both", key=f"sim_both_{user_id}", help="Simulate both Action + Comedy", use_container_width=True):
                # Add action to liked cache and comedy to search
                st.session_state.setdefault("recent_search_genres", set()).add("Comedy")
                meta_cache = st.session_state.setdefault("liked_meta_cache", {})
                meta_cache[50] = {"movie_id": 50, "movie_title": "Star Wars (1977)", "genres": "Action|Adventure|Sci-Fi"}
                st.session_state.setdefault(f"likes_set_{user_id}", set()).add(50)
                st.rerun()
        with t4:
            if st.button("↺", key=f"reset_sig_{user_id}", help="Reset Signals", use_container_width=True):
                clear_search_signals(user_id=user_id)
                st.session_state.pop(f"likes_set_{user_id}", None)
                st.session_state.pop("liked_meta_cache", None)
                st.rerun()

    # Render Cards in 6 Columns
    if movies:
        cols = st.columns(len(movies))
        for idx, m in enumerate(movies):
            with cols[idx]:
                render_movie_card(
                    movie=m,
                    user_id=user_id,
                    key_prefix=f"rec_foryou_{idx}",
                    show_score=False
                )
    else:
        render_empty_state("No Recommendations Found", "Try clearing filters or searching for another genre.")
