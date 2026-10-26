"""
Cinevora Discover Movies View (Cinematic Dark Edition)
Provides multi-attribute exploration across Cinevora's 1,682 movie catalog:
- Title keyword search with high-contrast input
- Hard genre constraint filtering
- Release year range slider (1922 to 1998)
- Sorting by popularity, rating, newest, or title
- Interactive movie cards with details popover and favorites/likes buttons
"""

import streamlit as st
from frontend.api_client import api_client
from frontend.components import render_header, render_movie_card, render_empty_state, render_footer
from frontend.config import ALL_GENRES
from frontend.suggested_service import record_search, record_genre_filter


def render_discover_page(user_id: str):
    """Renders the Discover Movies view in Cinematic Dark mode."""
    render_header("Catalog Discovery & Filter Engine")

    # Initial state setup from quick-browse or genre tile if present
    prefilter = st.session_state.pop("discover_prefilter_genre", None)
    if prefilter:
        st.session_state["discover_genre_filter"] = prefilter

    default_genre = st.session_state.get("discover_genre_filter", "All Genres")
    genre_options = ["All Genres"] + ALL_GENRES
    default_idx = genre_options.index(default_genre) if default_genre in genre_options else 0

    # Controls Bar
    with st.container():
        c1, c2, c3, c4 = st.columns([2.2, 1.4, 1.4, 1.0])

        with c1:
            initial_q = st.session_state.pop("discover_search_input", "")
            query = st.text_input(
                "Search Title",
                value=initial_q,
                placeholder="Search movies, genres, or discover your next favorite...",
                label_visibility="collapsed"
            )

        with c2:
            selected_genre = st.selectbox(
                "Genre Filter",
                genre_options,
                index=default_idx,
                label_visibility="collapsed"
            )

        with c3:
            sort_label = st.selectbox(
                "Sort By",
                ["Most Popular", "Highest Rated", "Newest", "Title (A–Z)"],
                index=0,
                label_visibility="collapsed"
            )
            sort_map = {
                "Most Popular": "popularity",
                "Highest Rated": "rating",
                "Newest": "newest",
                "Title (A–Z)": "title"
            }
            sort_by = sort_map[sort_label]

        with c4:
            items_per_page = st.selectbox("Per Page", [12, 24, 36], index=0, label_visibility="collapsed")

    # Secondary Filter Bar: Region & Language & Release Year Range
    with st.expander("🌐 Cinema Region, Language & Release Year Filters", expanded=False):
        r_c1, r_c2, r_c3 = st.columns([1.5, 1.5, 3.0])
        with r_c1:
            selected_region = st.selectbox(
                "Cinema Region",
                options=["All Regions", "Indian", "Hollywood", "International"],
                key="discover_region_filter"
            )
        with r_c2:
            lang_options = {
                "All Languages": None,
                "Tamil (ta)": "ta",
                "Telugu (te)": "te",
                "Malayalam (ml)": "ml",
                "Kannada (kn)": "kn",
                "Hindi (hi)": "hi",
                "English (en)": "en"
            }
            selected_lang_label = st.selectbox(
                "Language",
                options=list(lang_options.keys()),
                key="discover_lang_filter"
            )
            selected_lang_code = lang_options[selected_lang_label]
        with r_c3:
            year_range = st.slider(
                "Release Year Window",
                min_value=1922,
                max_value=2026,
                value=(1922, 2026),
                step=1,
                help="Filters movies by their production/release year."
            )

    # Page offset state
    page_key = "discover_page_num"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    current_offset = st.session_state[page_key] * items_per_page

    # Query API
    start_year = year_range[0] if year_range != (1922, 2026) else None
    end_year = year_range[1] if year_range != (1922, 2026) else None

    with st.spinner("Filtering catalog..."):
        data = api_client.search_movies(
            query=query,
            genre=selected_genre,
            region=selected_region if selected_region != "All Regions" else None,
            language=selected_lang_code,
            start_year=start_year,
            end_year=end_year,
            sort_by=sort_by,
            limit=items_per_page,
            offset=current_offset
        )

    total_count = data.get("count", 0)
    movies = data.get("results", [])

    # Record active search signals for Suggested Movies panel & SQLite history
    if query and query.strip():
        record_search(query.strip(), results=movies, user_id=user_id)
    if selected_genre and selected_genre != "All Genres":
        record_genre_filter(selected_genre)

    # Results Header & Active Constraints Notice
    filter_tags = []
    if selected_genre != "All Genres":
        filter_tags.append(f"Genre: {selected_genre}")
    if year_range != (1922, 1998):
        filter_tags.append(f"Years: {year_range[0]}–{year_range[1]}")
    if query:
        filter_tags.append(f'Keyword: "{query}"')

    tags_repr = f" • Filters: {', '.join(filter_tags)}" if filter_tags else ""

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            f'<div style="font-size: 1.15rem; font-weight: 700; color: #171923; margin: 12px 0 6px 0;">'
            f'Found {total_count} matching movies <span style="font-size: 0.85rem; color: #667085; font-weight: 400;">{tags_repr}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_h2:
        total_pages = max(1, (total_count + items_per_page - 1) // items_per_page)
        curr_p = st.session_state[page_key]
        p_c1, p_c2, p_c3 = st.columns([1, 1.4, 1])
        with p_c1:
            if st.button("◀", key="disc_prev_btn", disabled=(curr_p <= 0), use_container_width=True):
                st.session_state[page_key] = max(0, curr_p - 1)
                st.rerun()
        with p_c2:
            st.markdown(
                f'<div style="text-align: center; font-size: 0.82rem; color: #667085; padding-top: 6px;">'
                f'Page {curr_p + 1}/{total_pages}</div>',
                unsafe_allow_html=True
            )
        with p_c3:
            if st.button("▶", key="disc_next_btn", disabled=(curr_p >= total_pages - 1), use_container_width=True):
                st.session_state[page_key] = min(total_pages - 1, curr_p + 1)
                st.rerun()

    # Movie Cards Grid (Streaming 4-Column Poster Grid)
    if movies:
        cols = st.columns(4)
        for i, movie in enumerate(movies):
            with cols[i % 4]:
                render_movie_card(
                    movie=movie,
                    user_id=user_id,
                    key_prefix=f"discover_card_{current_offset + i}",
                    show_score=False
                )
    else:
        render_empty_state(
            title="No Matching Movies Found",
            message="No films match your search parameters. Try clearing some filters or searching for broader terms."
        )

    render_footer()
