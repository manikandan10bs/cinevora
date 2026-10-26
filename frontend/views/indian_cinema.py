"""
Cinevora Indian Cinema Exploration View (Tamil, Telugu, Malayalam, Kannada, Hindi)
Features:
- Dedicated spotlight banner for Indian cinema blockbusters (RRR, Vikram, Kantara, etc.)
- Multi-language tabs: All Indian, Tamil, Telugu, Malayalam, Kannada, Hindi
- Genre, release year, and rating filtering
- Multi-card horizontal trending carousel
- Responsive cinema card grid with 2:3 verified posters and instant like/watchlist actions
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
        get_indian_movies,
        get_movies_by_language,
        extract_release_year
    )
except ImportError:
    from poster_service import (  # type: ignore
        get_indian_movies,
        get_movies_by_language,
        extract_release_year
    )
from frontend.config import ALL_GENRES


def render_indian_cinema_page(user_id: str):
    """Renders the Indian Cinema dedicated discovery hub."""
    st.markdown(
        """
        <div style="margin-bottom: 22px;">
            <div style="font-family: 'Cinzel', serif; font-size: 2.2rem; font-weight: 800; color: #171923; letter-spacing: 0.02em; line-height: 1.1;">
                🇮🇳 Indian Cinema Showcase
            </div>
            <div style="color: #667085; font-size: 0.95rem; margin-top: 4px;">
                Explore celebrated blockbusters and modern cinematic gems across Tamil, Telugu, Malayalam, Kannada, and Hindi cinema.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------------------
    # 1. Trending Indian Movies Carousel (Top blockbusters)
    # -------------------------------------------------------------------------
    trending_indian = get_indian_movies()
    render_movie_carousel(
        title="🔥 Trending Indian Blockbusters",
        subtitle="Record-breaking pan-Indian sensations and critically acclaimed masterpieces",
        movies=trending_indian,
        user_id=user_id,
        section_id="indian_trending",
        limit_per_page=6
    )

    st.markdown('<hr style="border: none; border-bottom: 1px solid #E5E7EB; margin: 24px 0 18px 0;">', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. Language Navigation Tabs
    # -------------------------------------------------------------------------
    lang_tabs = [
        "All Indian",
        "Tamil (தமிழ்)",
        "Telugu (తెలుగు)",
        "Malayalam (മലയാളം)",
        "Kannada (ಕನ್ನಡ)",
        "Hindi (हिन्दी)"
    ]
    lang_code_map = {
        "All Indian": None,
        "Tamil (தமிழ்)": "ta",
        "Telugu (తెలుగు)": "te",
        "Malayalam (മലയാളം)": "ml",
        "Kannada (ಕನ್ನಡ)": "kn",
        "Hindi (हिन्दी)": "hi"
    }

    selected_lang_tab = st.radio(
        "Indian Language Filter",
        options=lang_tabs,
        horizontal=True,
        key="indian_lang_tab_radio",
        label_visibility="collapsed"
    )
    active_code = lang_code_map.get(selected_lang_tab)

    # -------------------------------------------------------------------------
    # 3. Filter Bar (Genre, Year Range, Min Rating, Sorting)
    # -------------------------------------------------------------------------
    f_c1, f_c2, f_c3, f_c4 = st.columns([2.5, 2.5, 2.5, 2.5])

    with f_c1:
        sel_genre = st.selectbox(
            "Genre",
            options=["All Genres"] + ALL_GENRES,
            key="indian_genre_filter"
        )
    with f_c2:
        year_span = st.slider(
            "Release Year",
            min_value=2000,
            max_value=2026,
            value=(2008, 2026),
            key="indian_year_slider"
        )
    with f_c3:
        min_rating = st.slider(
            "Minimum Rating",
            min_value=3.0,
            max_value=5.0,
            value=3.5,
            step=0.1,
            key="indian_min_rating"
        )
    with f_c4:
        sort_choice = st.selectbox(
            "Sort Order",
            options=["rating_desc", "newest", "title"],
            format_func=lambda s: {
                "rating_desc": "Highest Rated",
                "newest": "Newest Release",
                "title": "Alphabetical Title"
            }.get(s, s),
            key="indian_sort_choice"
        )

    # -------------------------------------------------------------------------
    # 4. Filter & Sort Execution
    # -------------------------------------------------------------------------
    candidates = get_indian_movies(language=active_code)

    # Apply genre filter
    if sel_genre != "All Genres":
        candidates = [m for m in candidates if sel_genre.lower() in str(m.get("genres", "")).lower()]

    # Apply year filter
    candidates = [m for m in candidates if extract_release_year(m) is not None and year_span[0] <= extract_release_year(m) <= year_span[1]]

    # Apply rating filter
    candidates = [m for m in candidates if float(m.get("avg_rating", 4.0)) >= min_rating]

    # Apply sorting
    if sort_choice == "rating_desc":
        candidates.sort(key=lambda m: float(m.get("avg_rating", 0.0)), reverse=True)
    elif sort_choice == "newest":
        candidates.sort(key=lambda m: extract_release_year(m, default=0) or 0, reverse=True)
    elif sort_choice == "title":
        candidates.sort(key=lambda m: str(m.get("title", "")).lower())

    # -------------------------------------------------------------------------
    # 5. Render Movie Catalog Grid
    # -------------------------------------------------------------------------
    st.markdown(
        f"""
        <div style="margin: 16px 0 14px 0; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
                <span style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #171923;">
                    {html.escape(selected_lang_tab)} Titles
                </span>
                <span style="color: #667085; font-size: 0.85rem; margin-left: 8px;">
                    ({len(candidates)} verified movies available)
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not candidates:
        render_empty_state(
            title="No Indian Movies Match These Filters",
            message="Try widening your release year window, adjusting the minimum rating, or clearing the genre filter.",
            icon="🇮🇳"
        )
    else:
        # Render in 4-column responsive grid
        cols_per_row = 4
        for row_idx in range(0, len(candidates), cols_per_row):
            batch = candidates[row_idx : row_idx + cols_per_row]
            grid_cols = st.columns(cols_per_row)
            for col_idx, movie in enumerate(batch):
                with grid_cols[col_idx]:
                    render_movie_card(
                        movie,
                        user_id=user_id,
                        key_prefix=f"ind_grid_{row_idx}_{col_idx}"
                    )

    # Footer
    render_footer()
