"""
Cinevora Hollywood Cinema Exploration View
Features:
- Spotlight blockbusters (Interstellar, The Dark Knight, Inception, Oppenheimer, Dune 2)
- Category filters: All Hollywood, Action & Sci-Fi, Drama & Romance, Crime & Thrillers, 90s Classics
- Release year filter spanning classic era (1920-1998) to modern blockbusters (2000-2026)
- Multi-card horizontal carousel for top Hollywood hits
- Responsive 4-column poster grid with interactive cards
"""

import html
import streamlit as st

from frontend.components import (
    render_movie_card,
    render_movie_carousel,
    render_empty_state,
    render_footer
)
try:
    from frontend.poster_service import (
        get_hollywood_movies,
        extract_release_year
    )
except ImportError:
    from poster_service import (  # type: ignore
        get_hollywood_movies,
        extract_release_year
    )
from frontend.api_client import api_client
from frontend.config import ALL_GENRES


def render_hollywood_page(user_id: str):
    """Renders the Hollywood dedicated discovery hub."""
    st.markdown(
        """
        <div style="margin-bottom: 22px;">
            <div style="font-family: 'Cinzel', serif; font-size: 2.2rem; font-weight: 800; color: #171923; letter-spacing: 0.02em; line-height: 1.1;">
                🎬 Hollywood & Global Classics
            </div>
            <div style="color: #667085; font-size: 0.95rem; margin-top: 4px;">
                Experience Hollywood's most acclaimed masterpieces, visionary sci-fi spectacles, and golden age cinematic icons.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------------------
    # 1. Hollywood Spotlight Carousel (Modern Blockbusters + Top Classics)
    # -------------------------------------------------------------------------
    modern_hollywood = [
        m for m in get_hollywood_movies()
        if (extract_release_year(m) or 0) >= 2000
    ]
    # Augment with top MovieLens blockbusters
    top_classic_resp = api_client.search_movies(sort_by="popularity", limit=12)
    top_classics = top_classic_resp.get("results", [])

    carousel_hollywood = modern_hollywood + top_classics[:8]

    render_movie_carousel(
        title="🌟 Hollywood Blockbusters & Legends",
        subtitle="Iconic cinematic achievements spanning modern epics to timeless milestones",
        movies=carousel_hollywood,
        user_id=user_id,
        section_id="hollywood_spotlight",
        limit_per_page=6
    )

    st.markdown('<hr style="border: none; border-bottom: 1px solid #E5E7EB; margin: 24px 0 18px 0;">', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. Quick Category Filter Pills
    # -------------------------------------------------------------------------
    category_tabs = [
        "All Hollywood",
        "Action & Sci-Fi",
        "Drama & Romance",
        "Crime & Thriller",
        "Golden Era (90s Classics)"
    ]

    selected_category = st.radio(
        "Hollywood Category",
        options=category_tabs,
        horizontal=True,
        key="hollywood_cat_radio",
        label_visibility="collapsed"
    )

    # -------------------------------------------------------------------------
    # 3. Filter Bar (Genre, Year Range, Min Rating, Sorting)
    # -------------------------------------------------------------------------
    f_c1, f_c2, f_c3, f_c4 = st.columns([2.5, 2.5, 2.5, 2.5])

    with f_c1:
        sel_genre = st.selectbox(
            "Genre",
            options=["All Genres"] + ALL_GENRES,
            key="hollywood_genre_filter"
        )
    with f_c2:
        year_span = st.slider(
            "Release Year",
            min_value=1920,
            max_value=2026,
            value=(1970, 2026),
            key="hollywood_year_slider"
        )
    with f_c3:
        min_rating = st.slider(
            "Minimum Rating",
            min_value=1.0,
            max_value=5.0,
            value=3.5,
            step=0.1,
            key="hollywood_min_rating"
        )
    with f_c4:
        sort_choice = st.selectbox(
            "Sort Order",
            options=["popularity", "rating_desc", "newest", "title"],
            format_func=lambda s: {
                "popularity": "Most Popular",
                "rating_desc": "Highest Rated",
                "newest": "Newest Release",
                "title": "Alphabetical Title"
            }.get(s, s),
            key="hollywood_sort_choice"
        )

    # -------------------------------------------------------------------------
    # 4. Candidate Retrieval & Filtering
    # -------------------------------------------------------------------------
    # Query backend catalog if querying historical classic range, or combine with enriched modern
    modern_matches = [
        m for m in get_hollywood_movies()
        if extract_release_year(m) is not None and year_span[0] <= extract_release_year(m) <= year_span[1]
    ]

    # Query API client for MovieLens catalog
    genre_param = None
    if sel_genre != "All Genres":
        genre_param = sel_genre
    elif selected_category == "Action & Sci-Fi":
        genre_param = "Action,Sci-Fi"
    elif selected_category == "Drama & Romance":
        genre_param = "Drama,Romance"
    elif selected_category == "Crime & Thriller":
        genre_param = "Crime,Thriller"

    # Restrict year for 90s category
    req_start_y = 1990 if selected_category == "Golden Era (90s Classics)" else year_span[0]
    req_end_y = 1999 if selected_category == "Golden Era (90s Classics)" else min(year_span[1], 1998)

    api_res = api_client.search_movies(
        genre=genre_param,
        start_year=max(1920, req_start_y),
        end_year=req_end_y,
        sort_by="popularity" if sort_choice == "popularity" else "rating" if sort_choice == "rating_desc" else sort_choice,
        limit=24
    )
    catalog_matches = api_res.get("results", [])

    # Filter modern matches according to genre / category
    if genre_param:
        g_targets = [g.strip().lower() for g in genre_param.split(",")]
        modern_matches = [
            m for m in modern_matches
            if any(gt in str(m.get("genres", "")).lower() for gt in g_targets)
        ]

    # Merge candidates (prioritize modern spotlight, then catalog results)
    combined = modern_matches + catalog_matches

    # Filter by minimum rating
    candidates = [
        m for m in combined
        if float(m.get("avg_rating") or m.get("predicted_rating") or 4.0) >= min_rating
    ]

    # Sorting
    if sort_choice == "rating_desc":
        candidates.sort(key=lambda m: float(m.get("avg_rating") or m.get("predicted_rating") or 0.0), reverse=True)
    elif sort_choice == "newest":
        candidates.sort(key=lambda m: extract_release_year(m, default=0) or 0, reverse=True)
    elif sort_choice == "title":
        candidates.sort(key=lambda m: str(m.get("title") or m.get("movie_title", "")).lower())

    # Deduplicate by movie_id / catalog_id
    seen_ids = set()
    deduped = []
    for m in candidates:
        m_id = str(m.get("catalog_id") or m.get("movie_id", "")).strip()
        if m_id and m_id not in seen_ids:
            seen_ids.add(m_id)
            deduped.append(m)

    # -------------------------------------------------------------------------
    # 5. Render Grid
    # -------------------------------------------------------------------------
    st.markdown(
        f"""
        <div style="margin: 16px 0 14px 0; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
                <span style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #171923;">
                    {html.escape(selected_category)} Titles
                </span>
                <span style="color: #667085; font-size: 0.85rem; margin-left: 8px;">
                    ({len(deduped)} movies displayed)
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not deduped:
        render_empty_state(
            title="No Hollywood Movies Found",
            message="Try widening your release year window or lowering the minimum rating filter.",
            icon="🎬"
        )
    else:
        cols_per_row = 4
        for row_idx in range(0, min(len(deduped), 24), cols_per_row):
            batch = deduped[row_idx : row_idx + cols_per_row]
            grid_cols = st.columns(cols_per_row)
            for col_idx, movie in enumerate(batch):
                with grid_cols[col_idx]:
                    render_movie_card(
                        movie,
                        user_id=user_id,
                        key_prefix=f"hwd_grid_{row_idx}_{col_idx}"
                    )

    # Footer
    render_footer()
