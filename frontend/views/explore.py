"""
Cinevora Master Movie Explore Page
Provides a dedicated, streaming-style discovery view for the 3,560-title master dataset:
- Bollywood, Kollywood (Tamil), Tollywood (Telugu), Mollywood (Malayalam),
  Sandalwood (Kannada), and Hollywood.
- Responsive card grids with 5-star ratings, industry badges, and dark streaming theme.
- Title search, multi-industry filtering with alias normalization, genre filters, and release year bounds.
- Sorting by rating, newest release, and alphabetical title.
- Resilient pagination with page selectors.
- Graceful poster fallbacks with onerror handlers.
- Rich movie details view showing cast, director, rating, genres, and official trailer link.
- Seamless Watchlist and Like persistence using safe unique 'catalog_id'.
"""

import html
import re
from typing import Dict, Any, List, Optional
import streamlit as st

from frontend.api_client import api_client
from frontend.components import render_header, render_empty_state, render_movie_card
from src.catalog_service import (
    query_master_catalog,
    get_master_catalog_stats,
    normalize_industry_filter
)

ITEMS_PER_PAGE = 24


def _get_star_rating_html(rating_10: float) -> str:
    """Converts a 10-point scale rating into 5 star glyphs."""
    rating_5 = rating_10 / 2.0
    stars = []
    for s_i in range(1, 6):
        if rating_5 >= s_i:
            stars.append("★")
        elif rating_5 >= s_i - 0.5:
            stars.append("★")
        else:
            stars.append("☆")
    return "".join(stars)


def render_master_movie_card(
    movie: Dict[str, Any],
    user_id: str,
    key_prefix: str = "explore"
):
    """
    Renders an individual master movie card using the unified cinematic movie card:
    - Clickable 2:3 poster leading directly to Movie Details
    - Direct ▶ Play button with official trailer or YouTube search fallback
    - ℹ️ Info button triggering the comprehensive Movie Details modal with same-genre related movies
    - Interactive Like & Watchlist buttons
    """
    render_movie_card(movie=movie, user_id=user_id, key_prefix=key_prefix)


def render_explore_page(user_id: str):
    """
    Renders the dedicated Movies / Explore page for Cinevora.
    """
    render_header("Explore Master Movie Catalog — Indian Cinema & Hollywood")

    stats = get_master_catalog_stats()
    total_in_db = stats.get("total_movies", 3560)

    # -------------------------------------------------------------------------
    # SEARCH BAR & QUICK FILTERS
    # -------------------------------------------------------------------------
    sc1, sc2, sc3 = st.columns([6, 1.2, 0.8])
    with sc1:
        query_input = st.text_input(
            "Search Catalog",
            value=st.session_state.get("explore_search_input", ""),
            placeholder=f"Search across {total_in_db:,} movies by title, cast, or director...",
            key="explore_search_bar_input",
            label_visibility="collapsed"
        )
    with sc2:
        search_clicked = st.button("🔍 Search", key="explore_exec_search_btn", type="primary", use_container_width=True)
    with sc3:
        clear_clicked = st.button("✕", key="explore_clear_search_btn", help="Clear search", use_container_width=True)
        if clear_clicked:
            st.session_state["explore_search_input"] = ""
            st.session_state["explore_page_index"] = 0
            st.rerun()

    active_query = query_input.strip() if query_input else ""
    if active_query and (search_clicked or st.session_state.get("explore_search_input") != active_query):
        st.session_state["explore_search_input"] = active_query
        st.session_state["explore_page_index"] = 0

    # -------------------------------------------------------------------------
    # QUICK INDUSTRY PILLS (1-Click Filters)
    # -------------------------------------------------------------------------
    industry_pills = [
        ("All", "All Industries"),
        ("Bollywood", "Bollywood (Hindi)"),
        ("Tamil", "Kollywood (Tamil)"),
        ("Telugu", "Tollywood (Telugu)"),
        ("Malayalam", "Mollywood (Malayalam)"),
        ("Kannada", "Sandalwood (Kannada)"),
        ("Hollywood", "Hollywood")
    ]

    selected_pill = st.session_state.get("explore_active_industry_pill", "All")
    pill_cols = st.columns(len(industry_pills))

    for idx, (canonical, label) in enumerate(industry_pills):
        with pill_cols[idx]:
            btn_type = "primary" if selected_pill == canonical else "secondary"
            if st.button(label, key=f"pill_ind_{canonical}", type=btn_type, use_container_width=True):
                st.session_state["explore_active_industry_pill"] = canonical
                st.session_state["explore_page_index"] = 0
                st.rerun()

    # -------------------------------------------------------------------------
    # DETAILED FILTER DRAWER
    # -------------------------------------------------------------------------
    with st.expander("⚙️ Refine Catalog Filters & Sorting", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)

        with fc1:
            all_genres = ["All Genres"] + stats.get("genres", [])
            sel_genre = st.selectbox(
                "Filter by Genre",
                options=all_genres,
                index=0,
                key="explore_genre_select"
            )

        with fc2:
            sort_options = ["Highest Rated", "Newest Release", "Alphabetical (A-Z)"]
            sel_sort = st.selectbox(
                "Sort Results",
                options=sort_options,
                index=0,
                key="explore_sort_select"
            )

        with fc3:
            y_min = stats.get("year_min", 2021)
            y_max = stats.get("year_max", 2025)
            year_bounds = st.slider(
                "Release Year Span",
                min_value=y_min,
                max_value=y_max,
                value=(y_min, y_max),
                key="explore_year_bounds"
            )

        with fc4:
            min_rating_val = st.slider(
                "Minimum Viewer Rating (1-10)",
                min_value=0.0,
                max_value=10.0,
                value=0.0,
                step=0.5,
                key="explore_min_rating"
            )

    # Resolve active filter parameters
    effective_industry = None if selected_pill == "All" else selected_pill
    effective_genre = None if sel_genre == "All Genres" else sel_genre
    effective_min_year = year_bounds[0]
    effective_max_year = year_bounds[1]

    sort_map = {
        "Highest Rated": "rating",
        "Newest Release": "newest",
        "Alphabetical (A-Z)": "title"
    }
    effective_sort = sort_map.get(sel_sort, "rating")

    # Pagination state
    if "explore_page_index" not in st.session_state:
        st.session_state["explore_page_index"] = 0

    current_page = st.session_state["explore_page_index"]
    offset = current_page * ITEMS_PER_PAGE

    # Query master catalog
    movies, total_count = query_master_catalog(
        query=st.session_state.get("explore_search_input", ""),
        industry=effective_industry,
        genre=effective_genre,
        start_year=effective_min_year,
        end_year=effective_max_year,
        min_rating=min_rating_val,
        sort_by=effective_sort,
        limit=ITEMS_PER_PAGE,
        offset=offset
    )

    if active_query and movies:
        try:
            from frontend.suggested_service import record_search
            record_search(active_query, results=movies, user_id=user_id)
        except Exception:
            pass

    total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    if current_page >= total_pages:
        current_page = 0
        st.session_state["explore_page_index"] = 0
        offset = 0

    # -------------------------------------------------------------------------
    # RESULTS HEADER & PAGINATION CONTROLS
    # -------------------------------------------------------------------------
    st.markdown('<div class="cinevora-section-divider" style="margin-top: 14px; margin-bottom: 14px;"></div>', unsafe_allow_html=True)

    hdr_col1, hdr_col2 = st.columns([3.5, 2.5])

    with hdr_col1:
        ind_label = f" in {selected_pill}" if selected_pill != "All" else ""
        query_label = f' matching "{active_query}"' if active_query else ""
        st.markdown(
            f"""
            <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 800; color: #FFFFFF;">
                Showing {len(movies)} of {total_count:,} Titles{html.escape(ind_label)}{html.escape(query_label)}
            </div>
            <div style="font-size: 0.82rem; color: #9CA3AF;">
                Page {current_page + 1} of {total_pages} • Sorted by {sel_sort}
            </div>
            """,
            unsafe_allow_html=True
        )

    with hdr_col2:
        if total_pages > 1:
            prev_c, num_c, next_c = st.columns([1, 1.6, 1])
            with prev_c:
                if st.button("◀ Prev", key="explore_prev_page", disabled=(current_page == 0), use_container_width=True):
                    st.session_state["explore_page_index"] = max(0, current_page - 1)
                    st.rerun()
            with num_c:
                st.markdown(
                    f'<div style="text-align: center; color: #E2E8F0; font-size: 0.85rem; padding-top: 8px; font-weight: 600;">'
                    f'Page {current_page + 1} / {total_pages}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with next_c:
                if st.button("Next ▶", key="explore_next_page", disabled=(current_page >= total_pages - 1), use_container_width=True):
                    st.session_state["explore_page_index"] = min(total_pages - 1, current_page + 1)
                    st.rerun()

    # -------------------------------------------------------------------------
    # RESPONSIVE MOVIE CARDS GRID
    # -------------------------------------------------------------------------
    if movies:
        # Display in rows of 6 cards across
        row_size = 6
        for r_idx in range(0, len(movies), row_size):
            chunk = movies[r_idx : r_idx + row_size]
            cols = st.columns(len(chunk))
            for c_idx, movie in enumerate(chunk):
                with cols[c_idx]:
                    render_master_movie_card(
                        movie=movie,
                        user_id=user_id,
                        key_prefix=f"exp_p{current_page}_{r_idx + c_idx}"
                    )
            st.write("")

        # Bottom Pagination
        if total_pages > 1:
            st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)
            b_prev, b_info, b_next = st.columns([1, 3, 1])
            with b_prev:
                if st.button("◀ Previous Page", key="explore_bot_prev", disabled=(current_page == 0), use_container_width=True):
                    st.session_state["explore_page_index"] = max(0, current_page - 1)
                    st.rerun()
            with b_info:
                st.markdown(
                    f'<div style="text-align: center; color: #9CA3AF; font-size: 0.85rem; padding-top: 8px;">'
                    f'Showing items {offset + 1}–{min(total_count, offset + len(movies))} of {total_count:,} movies'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with b_next:
                if st.button("Next Page ▶", key="explore_bot_next", disabled=(current_page >= total_pages - 1), use_container_width=True):
                    st.session_state["explore_page_index"] = min(total_pages - 1, current_page + 1)
                    st.rerun()

    else:
        render_empty_state(
            title="No Movies Found Matching Your Criteria",
            message="Try widening your release year span, resetting the minimum rating threshold, or searching for a different title."
        )
