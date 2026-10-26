"""
Cinevora UI Components Module (Cinematic Streaming Edition)
Recreates the reference streaming layout (Prime Video / Modern Cinema):
- Narrow Left Vertical Icon Rail (in st.sidebar)
- Edge-to-Edge Cinematic Hero Spotlight with backdrop, gold stars, badges, synopsis, and action buttons
- Top 10 Ranked Movie Carousel with giant translucent numbers (1, 2, 3...) behind cards
- Horizontal Streaming Movie Carousels with bug-free < and > navigation
- Interactive 2:3 Movie Cards with Details Modal (YouTube trailer embed, cast, director, similar titles)
- Explore by Genre category tiles
- High-contrast dark metric cards and empty states
- Cinevora Streaming Footer
"""

import html
import re
from typing import Dict, Any, Optional, List, Union
import streamlit as st

from frontend.api_client import api_client
from frontend.config import ALL_GENRES
from frontend.poster_service import (
    render_poster_html,
    get_poster_url,
    get_backdrop_url,
    get_movie_synopsis,
    get_trailer_url,
    get_effective_trailer_url,
    get_same_genre_movies,
    get_featured_movies,
    get_movie_enrichment,
    extract_release_year
)


# -----------------------------------------------------------------------------
# 1. Left Vertical Icon Navigation Rail
# -----------------------------------------------------------------------------
def render_vertical_nav_rail(active_page: str, user_id: str):
    """
    Renders the narrow vertical icon navigation rail in the sidebar.
    Follows modern streaming design with sleek icon buttons, tooltips, and cyan active indicators.
    """
    with st.sidebar:
        # Profile / Account Avatar Button
        user_initial = user_id[:2].upper() if user_id else "U1"
        is_account = (active_page in ["Account", "Profile", "Login"])
        if st.button(
            "👤",
            key="rail_btn_account",
            help=f"User Profile & Account ({user_id})",
            type="primary" if is_account else "secondary",
            use_container_width=True
        ):
            st.session_state["nav_selection"] = "Account"
            st.rerun()

        # Navigation Destinations
        rail_destinations = [
            ("🏠", "Home", "Home — Cinematic Discovery"),
            ("🔍", "Search", "Search 3,560 Movies"),
            ("🍿", "Explore", "Explore All Cinema"),
            ("🎯", "Recommendations", "For You — Personalized Recommendations"),
            ("🔖", "Watchlist", "My Watchlist"),
            ("❤️", "Liked Movies", "Liked Movies"),
            ("📊", "Monitoring", "MLOps & System Health"),
            ("✨", "AI Concierge", "AI Movie Concierge (Gemini 3.5 Flash Lite)")
        ]

        for icon, dest_name, tooltip in rail_destinations:
            is_active = (active_page == dest_name) or (dest_name == "Watchlist" and active_page in ["My Watchlist", "Watchlist"])
            if st.button(
                icon,
                key=f"rail_btn_{dest_name}",
                help=tooltip,
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                if dest_name == "Search":
                    st.session_state["nav_selection"] = "Explore"
                    st.session_state["focus_search"] = True
                elif dest_name == "AI Concierge":
                    st.session_state["nav_selection"] = "AI Concierge"
                else:
                    st.session_state["nav_selection"] = dest_name
                st.rerun()

        # Live Backend Health Indicator at bottom of rail
        health = api_client.get_health()
        is_online = bool(health and health.get("status") == "healthy")
        dot_color = "#00E5FF" if is_online else "#EF4444"
        total_count = health.get("master_catalog_count", 3560) if is_online else 0
        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 28px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08);">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: {dot_color}; box-shadow: 0 0 8px {dot_color};"></span>
                <div style="font-size: 0.58rem; color: #64748B; font-weight: 700; text-transform: uppercase; margin-top: 2px;">
                    {'Online' if is_online else 'Offline'}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# -----------------------------------------------------------------------------
# 2. Interactive Movie Details Dialog (YouTube Trailer Embed, Metadata, Similar)
# -----------------------------------------------------------------------------
def _render_movie_details_modal_content(movie: Dict[str, Any], user_id: str):
    """Internal content renderer for the movie details dialog."""
    catalog_id = str(movie.get("catalog_id") or movie.get("movie_id") or "").strip()
    raw_title = str(movie.get("title") or movie.get("movie_title") or "Movie Details")
    clean_title = re.sub(r"\s*\(\d{4}\)", "", raw_title).strip()
    year = extract_release_year(movie, default=2023)
    genres_str = str(movie.get("genre") or movie.get("genres", "Cinema"))
    industry = str(movie.get("industry") or movie.get("cinema_region") or "Cinema")
    avg_rating = float(movie.get("rating") or movie.get("avg_rating") or 6.5)
    director = str(movie.get("director") or "Visionary Director")
    cast_str = str(movie.get("cast") or "Ensemble Cast")
    trailer_url = movie.get("trailer_link") or movie.get("trailer_url")
    poster_url = movie.get("movie_poster") or movie.get("poster_url")

    # If opened from AI Concierge, show navigation button back to chat
    if st.session_state.get("return_to_ai_dialog_after_details", False):
        if st.button("← Back to AI Concierge", key=f"back_to_ai_top_{catalog_id}", type="secondary"):
            st.session_state["show_movie_details"] = False
            st.session_state["show_ai_dialog"] = True
            st.session_state["return_to_ai_dialog_after_details"] = False
            st.rerun()

    # Record viewing event into SQLite database
    try:
        api_client.record_view(
            user_id=user_id,
            movie_id=catalog_id,
            movie_title=clean_title,
            genres=genres_str,
            industry=industry
        )
    except Exception:
        pass

    # Trailer video embed if available or search fallback
    trailer_url = get_effective_trailer_url(movie, clean_title)
    is_embeddable = bool(trailer_url and ("youtube.com/watch" in str(trailer_url) or "youtu.be/" in str(trailer_url)))

    if is_embeddable:
        try:
            st.video(trailer_url)
        except Exception:
            is_embeddable = False

    if not is_embeddable:
        if poster_url and str(poster_url).startswith("http"):
            st.markdown(
                f"""
                <div style="text-align: center; margin-bottom: 14px;">
                    <img src="{html.escape(poster_url)}" style="max-height: 280px; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.6);" />
                </div>
                """,
                unsafe_allow_html=True
            )
        st.link_button(
            "▶ Watch Trailer on YouTube",
            trailer_url,
            type="primary",
            use_container_width=True,
            help=f"Play trailer for {clean_title} on YouTube"
        )

    # Title, Badges, and Gold Stars
    ind_class = f"badge-{industry.lower()}"
    rating_5 = avg_rating / 2.0 if avg_rating > 5.0 else avg_rating
    stars_html = []
    for s_i in range(1, 6):
        if rating_5 >= s_i:
            stars_html.append("★")
        elif rating_5 >= s_i - 0.5:
            stars_html.append("★")
        else:
            stars_html.append("☆")
    stars_str = "".join(stars_html)

    st.markdown(
        f"""
        <div style="margin: 10px 0 16px 0;">
            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px; flex-wrap: wrap;">
                <span class="badge-industry {ind_class}">{html.escape(industry)}</span>
                <span style="font-size: 0.85rem; color: #94A3B8; font-weight: 600;">{year}</span>
                <span style="font-size: 0.85rem; color: #64748B;">•</span>
                <span style="font-size: 0.85rem; color: #CBD5E1;">{html.escape(genres_str)}</span>
                <span style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; padding: 1px 6px; font-size: 0.72rem; font-weight: 700; color: #F8FAFC;">18+</span>
            </div>
            <div style="font-family: 'Cinzel', serif; font-size: 1.8rem; font-weight: 800; color: #FFFFFF; line-height: 1.2;">
                {html.escape(clean_title)}
            </div>
            <div style="display: flex; align-items: center; gap: 10px; margin-top: 6px;">
                <span style="color: #FFB800; font-size: 1.15rem; letter-spacing: 2px;">{stars_str}</span>
                <span style="color: #FFFFFF; font-weight: 700; font-size: 1rem;">{avg_rating:.1f} / 10.0</span>
                <span style="color: #64748B; font-size: 0.8rem;">(Master Catalog Score)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Detailed Credits Box
    st.markdown(
        f"""
        <div style="background: #111A24; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.06); font-size: 0.9rem; line-height: 1.6;">
            <div><strong style="color: #00E5FF;">Directed by:</strong> <span style="color: #F8FAFC;">{html.escape(director)}</span></div>
            <div><strong style="color: #00E5FF;">Starring:</strong> <span style="color: #F8FAFC;">{html.escape(cast_str)}</span></div>
            <div style="margin-top: 8px; color: #94A3B8;">A critically acclaimed cinematic work from the {html.escape(industry)} film industry, cataloged in Cinevora's verified master dataset.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Watchlist & Like Action Buttons
    fav_key = f"fav_set_{user_id}"
    likes_key = f"likes_set_{user_id}"
    user_favs = st.session_state.setdefault(fav_key, set())
    user_likes = st.session_state.setdefault(likes_key, set())
    is_fav = catalog_id in user_favs
    is_liked = catalog_id in user_likes

    act_col1, act_col2, act_col3 = st.columns([1, 1, 1.2])
    with act_col1:
        fav_label = "🔖 In Watchlist" if is_fav else "➕ Add to Watchlist"
        if st.button(fav_label, key=f"modal_fav_{catalog_id}_{user_id}", use_container_width=True):
            if is_fav:
                api_client.remove_favorite(user_id, catalog_id)
                user_favs.discard(catalog_id)
                st.toast(f"Removed '{clean_title}' from Watchlist", icon="🗑️")
            else:
                api_client.add_favorite(
                    user_id=user_id,
                    movie_id=catalog_id,
                    movie_title=clean_title,
                    genres=genres_str,
                    release_date=str(year),
                    rating=avg_rating
                )
                user_favs.add(catalog_id)
                st.toast(f"Saved '{clean_title}' to Watchlist!", icon="🔖")
            st.rerun()

    with act_col2:
        like_label = "❤️ Liked" if is_liked else "🤍 Like Movie"
        if st.button(like_label, key=f"modal_like_{catalog_id}_{user_id}", use_container_width=True):
            liked_now = api_client.toggle_like(user_id, catalog_id)
            if liked_now:
                user_likes.add(catalog_id)
                st.toast(f"Liked '{clean_title}'!", icon="❤️")
            else:
                user_likes.discard(catalog_id)
                st.toast(f"Unliked '{clean_title}'", icon="🤍")
            st.rerun()

    with act_col3:
        st.link_button(
            "▶ Play Trailer",
            trailer_url,
            help=f"Play trailer for {clean_title}",
            use_container_width=True
        )

    # 4 Same-Genre Related Movies Row (Clickable image/button explores that movie)
    try:
        genre_list = [g.strip() for g in genres_str.replace(",", "|").split("|") if g.strip()]
        primary_genre = genre_list[0] if genre_list else "Cinema"
        related_movies = get_same_genre_movies(catalog_id=catalog_id, genres_str=genres_str, limit=4)
        if related_movies:
            st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; margin-top: 14px;">
                    <span style="font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">
                        🎬 Related {html.escape(primary_genre)} Movies
                    </span>
                    <span style="font-size: 0.74rem; color: #00E5FF; font-weight: 600;">Click any movie to view info & trailer</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            sim_cols = st.columns(min(len(related_movies), 4))
            for s_idx, sim_m in enumerate(related_movies):
                with sim_cols[s_idx]:
                    s_cid = str(sim_m.get("catalog_id") or sim_m.get("movie_id") or f"sim_{s_idx}")
                    s_title = str(sim_m.get("title") or "Movie")
                    s_clean = re.sub(r"\s*\(\d{4}\)", "", s_title).strip()
                    s_post = sim_m.get("movie_poster") or sim_m.get("poster_url") or "https://placehold.co/200x300/131B26/00E5FF?text=Cinevora"
                    s_yr = extract_release_year(sim_m, default="")
                    s_rat = float(sim_m.get("rating") or sim_m.get("avg_rating") or 6.5)
                    s_trailer = get_effective_trailer_url(sim_m, s_clean)

                    st.markdown(
                        f"""
                        <div style="background: #0E1622; border-radius: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); padding: 6px; text-align: center; margin-bottom: 6px;">
                            <img src="{html.escape(str(s_post))}" alt="{html.escape(s_clean)}" style="width: 100%; aspect-ratio: 2/3; object-fit: cover; border-radius: 6px; display: block;" onerror="this.src='https://placehold.co/200x300/131B26/00E5FF?text=Cinevora';" />
                            <div style="font-weight: 700; font-size: 0.8rem; color: #FFFFFF; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{html.escape(s_title)}">{html.escape(s_clean)}</div>
                            <div style="font-size: 0.72rem; color: #FFB800;">★ {s_rat:.1f} • {s_yr}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    sub_c1, sub_c2 = st.columns([1.2, 0.8])
                    with sub_c1:
                        if st.button("ℹ️ View", key=f"sim_view_{catalog_id}_{s_cid}_{s_idx}", use_container_width=True):
                            st.session_state["selected_movie_id"] = s_cid
                            st.session_state["selected_movie_data"] = sim_m
                            st.session_state["show_movie_details"] = True
                            st.rerun()
                    with sub_c2:
                        st.link_button("▶", s_trailer, key=f"sim_play_{catalog_id}_{s_cid}_{s_idx}", help=f"Play trailer for {s_clean}", use_container_width=True)
    except Exception:
        pass


def _on_movie_details_dismiss():
    """Callback executed when the movie details modal dialog is dismissed."""
    st.session_state["show_movie_details"] = False
    if st.session_state.pop("return_to_ai_dialog_after_details", False):
        st.session_state["show_ai_dialog"] = True


if hasattr(st, "dialog"):
    @st.dialog("🎬 Movie Details", width="large", on_dismiss=_on_movie_details_dismiss)
    def show_movie_details_dialog(movie: Dict[str, Any], user_id: str):
        """Displays modal movie details dialog with trailer and actions."""
        _render_movie_details_modal_content(movie, user_id)
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("🎬 Movie Details", width="large", on_dismiss=_on_movie_details_dismiss)
    def show_movie_details_dialog(movie: Dict[str, Any], user_id: str):
        """Displays modal movie details dialog with trailer and actions."""
        _render_movie_details_modal_content(movie, user_id)
else:
    def show_movie_details_dialog(movie: Dict[str, Any], user_id: str):
        """Fallback when st.dialog is not supported."""
        with st.expander("🎬 Movie Details", expanded=True):
            _render_movie_details_modal_content(movie, user_id)


# -----------------------------------------------------------------------------
# 3. Cinematic Full-Screen Streaming Hero Banner (Matching Reference Image)
# -----------------------------------------------------------------------------
def _on_hero_nav(delta: int, total_slides: int):
    """Callback to advance hero slide atomically."""
    current = st.session_state.get("hero_slide_index", 0)
    st.session_state["hero_slide_index"] = (current + delta) % max(1, total_slides)


def render_streaming_hero_banner(user_id: str):
    """
    Renders the cinematic edge-to-edge streaming hero banner directly inspired by modern streaming.
    - Large movie backdrop image occupying the viewport with dark gradient fade.
    - Stylized uppercase Cinzel title, gold rating stars, age badge, genres, and synopsis.
    - Action buttons: ▶ Watch Trailer, ℹ Details, ➕ Watchlist, ❤️ Like.
    - Clean slide controls with atomic session state updates.
    """
    featured_movies = get_featured_movies()
    if not featured_movies:
        return

    fav_cache_key = f"fav_set_{user_id}"
    likes_cache_key = f"likes_set_{user_id}"
    if fav_cache_key not in st.session_state:
        st.session_state[fav_cache_key] = set(str(f["movie_id"]).strip() for f in api_client.get_favorites(user_id))
    if likes_cache_key not in st.session_state:
        st.session_state[likes_cache_key] = set(str(mid).strip() for mid in api_client.get_likes(user_id))

    user_favs = st.session_state[fav_cache_key]
    user_likes = st.session_state[likes_cache_key]

    total_slides = len(featured_movies)
    if "hero_slide_index" not in st.session_state:
        st.session_state["hero_slide_index"] = 0

    slide_idx = st.session_state["hero_slide_index"] % total_slides
    movie = featured_movies[slide_idx]

    m_id = str(movie.get("catalog_id") or movie.get("movie_id") or "1").strip()
    title = str(movie.get("title") or movie.get("movie_title") or f"Movie #{m_id}")
    clean_title = re.sub(r"\s*\(\d{4}\)", "", title).strip()
    year = extract_release_year(movie, default=2023)
    genres_str = str(movie.get("genre") or movie.get("genres", "Cinema"))
    genres_display = " • ".join([g.strip() for g in genres_str.replace(",", "|").split("|") if g.strip()][:3])
    avg_rating = float(movie.get("avg_rating") or movie.get("rating") or 7.8)
    industry = str(movie.get("industry") or movie.get("cinema_region") or "Cinema")
    director = str(movie.get("director") or "Visionary Director")
    cast_str = str(movie.get("cast") or "Ensemble Cast")
    trailer_url = movie.get("trailer_link") or movie.get("trailer_url")
    poster_url = movie.get("movie_poster") or movie.get("poster_url")

    is_fav = m_id in user_favs
    is_liked = m_id in user_likes

    # 5 Gold Stars HTML
    rating_5 = avg_rating / 2.0 if avg_rating > 5.0 else avg_rating
    stars_html = []
    for s_i in range(1, 6):
        if rating_5 >= s_i:
            stars_html.append("★")
        elif rating_5 >= s_i - 0.5:
            stars_html.append("★")
        else:
            stars_html.append("☆")
    stars_str = "".join(stars_html)

    ind_badge_class = f"badge-{industry.lower()}"

    # Container with two columns: Content (left) and Featured Artwork (right)
    hero_col_left, hero_col_right = st.columns([1.5, 1.1])

    with hero_col_left:
        st.markdown(
            f"""
            <div style="padding: 10px 0 16px 0;">
                <div class="hero-brand-subtitle">CINEVORA SPOTLIGHT • {html.escape(industry.upper())}</div>
                <div class="hero-title-text">{html.escape(clean_title)}</div>
                <div class="hero-meta-row">
                    <span class="badge-industry {ind_badge_class}">{html.escape(industry)}</span>
                    <span class="hero-age-badge">18+</span>
                    <span style="font-weight: 700; color: #F8FAFC;">{year}</span>
                    <span style="color: #64748B;">•</span>
                    <span class="hero-stars">{stars_str}</span>
                    <span style="font-weight: 700; color: #FFFFFF;">{avg_rating:.1f}</span>
                    <span style="color: #64748B;">•</span>
                    <span style="color: #CBD5E1;">{html.escape(genres_display)}</span>
                </div>
                <div class="hero-synopsis-text">
                    Directed by <strong style="color: #FFFFFF;">{html.escape(director)}</strong>. 
                    Starring <strong style="color: #CBD5E1;">{html.escape(cast_str)}</strong>. 
                    A landmark cinematic experience celebrated across {html.escape(industry)} cinema.
                </div>
                <div class="hero-included-tag">
                    <span>✔</span> <span>Included with Cinevora Master Catalog</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Action Buttons Row
        b_c1, b_c2, b_c3, b_c4 = st.columns([1.6, 1.2, 1.1, 1.1])

        with b_c1:
            if trailer_url and ("youtube.com" in str(trailer_url) or "youtu.be" in str(trailer_url)):
                if st.button("▶ Watch Trailer", key=f"hero_play_btn_{m_id}", type="primary", use_container_width=True):
                    show_movie_details_dialog(movie, user_id)
            else:
                if st.button("▶ Watch Movie", key=f"hero_play_btn_{m_id}", type="primary", use_container_width=True):
                    show_movie_details_dialog(movie, user_id)

        with b_c2:
            fav_label = "🔖 Saved" if is_fav else "➕ Watchlist"
            if st.button(fav_label, key=f"hero_fav_{m_id}_{user_id}", use_container_width=True):
                if is_fav:
                    api_client.remove_favorite(user_id, m_id)
                    user_favs.discard(m_id)
                    st.toast(f"Removed '{clean_title}' from Watchlist", icon="🗑️")
                else:
                    api_client.add_favorite(
                        user_id=user_id,
                        movie_id=m_id,
                        movie_title=title,
                        genres=genres_str,
                        release_date=str(year),
                        rating=avg_rating
                    )
                    user_favs.add(m_id)
                    st.toast(f"Saved '{clean_title}' to Watchlist!", icon="🔖")
                st.rerun()

        with b_c3:
            like_label = "❤️ Liked" if is_liked else "🤍 Like"
            if st.button(like_label, key=f"hero_like_{m_id}_{user_id}", use_container_width=True):
                liked_now = api_client.toggle_like(user_id, m_id)
                if liked_now:
                    user_likes.add(m_id)
                    st.toast(f"Liked '{clean_title}'!", icon="❤️")
                else:
                    user_likes.discard(m_id)
                    st.toast(f"Unliked '{clean_title}'", icon="🤍")
                st.rerun()

        with b_c4:
            if st.button("ℹ Details", key=f"hero_details_btn_{m_id}", use_container_width=True):
                show_movie_details_dialog(movie, user_id)

        # Slide pagination controls
        st.write("")
        ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1, 2, 1])
        with ctrl_c1:
            st.button("‹ Prev", key="hero_prev_btn", on_click=_on_hero_nav, args=(-1, total_slides), use_container_width=True)
        with ctrl_c2:
            st.markdown(
                f'<div style="text-align: center; font-size: 0.82rem; color: #94A3B8; padding-top: 6px; font-weight: 600;">Featured {slide_idx + 1} of {total_slides}</div>',
                unsafe_allow_html=True
            )
        with ctrl_c3:
            st.button("Next ›", key="hero_next_btn", on_click=_on_hero_nav, args=(1, total_slides), use_container_width=True)

    with hero_col_right:
        if poster_url and str(poster_url).startswith("http"):
            st.markdown(
                f"""
                <div style="
                    position: relative;
                    max-width: 380px;
                    margin: 0 auto;
                    border-radius: 14px;
                    overflow: hidden;
                    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.8), 0 0 25px rgba(0, 229, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                ">
                    <a href="?action=movie_details&m_id={html.escape(m_id)}" target="_self" title="Click to view details for {html.escape(clean_title)}">
                        <img src="{html.escape(poster_url)}" alt="{html.escape(clean_title)}" style="width: 100%; height: auto; display: block; cursor: pointer;" onerror="this.src='https://placehold.co/400x550/131B26/00E5FF?text=Cinevora';" />
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_rotating_hero_banner(user_id: str):
    """Backwards-compatible wrapper."""
    render_streaming_hero_banner(user_id=user_id)


def render_hero_billboard(movie: Optional[Dict[str, Any]] = None, user_id: str = "demo_user_1"):
    """Backwards-compatible wrapper."""
    render_streaming_hero_banner(user_id=user_id)


# -----------------------------------------------------------------------------
# 4. Interactive Movie Card (2:3 Aspect Ratio, Gold Stars, Action Buttons)
# -----------------------------------------------------------------------------
def render_movie_card(
    movie: Dict[str, Any],
    user_id: str,
    key_prefix: str = "card",
    show_score: bool = False,
    in_dialog: bool = False
):
    """
    Renders an individual cinema movie card in the cinematic dark theme:
    - 2:3 aspect-ratio poster with lazy loading & onerror fallback
    - Clean uppercase title, release year, and industry badge
    - 5 gold stars rating system
    - Interactive Like, Watchlist, and Details modal triggers
    """
    catalog_id = str(movie.get("catalog_id") or movie.get("movie_id") or "").strip()
    raw_title = str(movie.get("title") or movie.get("movie_title") or "Untitled")
    clean_title = re.sub(r"\s*\(\d{4}\)", "", raw_title).strip()
    year = extract_release_year(movie, default=2023)
    genres_str = str(movie.get("genre") or movie.get("genres", "Cinema"))
    industry = str(movie.get("industry") or movie.get("cinema_region") or "Cinema")
    rating_val = float(movie.get("rating") or movie.get("avg_rating") or movie.get("predicted_rating") or 6.5)
    score = movie.get("score")
    suggestion_reason = movie.get("suggestion_reason")
    poster_url = movie.get("movie_poster") or movie.get("poster_url")

    # 5 Gold Stars HTML
    rating_5 = rating_val / 2.0 if rating_val > 5.0 else rating_val
    stars_html = []
    for s_i in range(1, 6):
        if rating_5 >= s_i:
            stars_html.append("★")
        elif rating_5 >= s_i - 0.5:
            stars_html.append("★")
        else:
            stars_html.append("☆")
    stars_str = "".join(stars_html)

    # First genre tag
    genre_tokens = [g.strip() for g in genres_str.replace(",", "|").split("|") if g.strip()]
    primary_genre = genre_tokens[0] if genre_tokens else "Cinema"

    ind_badge_class = f"badge-{industry.lower()}"

    # Reason pill if suggested
    reason_html = f'<div style="margin-bottom: 4px;"><span class="taste-badge">✨ {html.escape(suggestion_reason)}</span></div>' if suggestion_reason else ""

    effective_trailer_url = get_effective_trailer_url(movie, clean_title)

    # Poster markup (2:3 aspect ratio) with clickable anchor
    poster_element = render_poster_html(
        movie_id=catalog_id,
        title=clean_title,
        release_date=str(year),
        genres=genres_str,
        poster_url=poster_url
    )

    card_html = (
        f'<div class="movie-card">'
        f'<a href="?action=movie_details&m_id={html.escape(catalog_id)}" target="_self" style="text-decoration: none; color: inherit; display: block; cursor: pointer;" title="Click to view details & trailer for {html.escape(clean_title)}">'
        f'{poster_element}'
        f'</a>'
        f'<div class="movie-card-body">'
        f'{reason_html}'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
        f'<span class="badge-industry {ind_badge_class}">{html.escape(industry)}</span>'
        f'<span style="font-size: 0.78rem; color: #94A3B8; font-weight: 600;">{year}</span>'
        f'</div>'
        f'<a href="?action=movie_details&m_id={html.escape(catalog_id)}" target="_self" style="text-decoration: none; color: inherit; display: block;" title="Click to view details & trailer for {html.escape(clean_title)}">'
        f'<div class="movie-title-text" title="{html.escape(raw_title)}">{html.escape(clean_title)}</div>'
        f'</a>'
        f'<div class="movie-red-stars" style="color: #FFB800;">{stars_str} <span class="meta-rating" style="color: #F8FAFC;">{rating_val:.1f}</span></div>'
        f'<div class="movie-card-meta"><span>{html.escape(primary_genre)}</span></div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Interactive Action Buttons Row (Play, Info/Details, Like, Watchlist)
    fav_cache_key = f"fav_set_{user_id}"
    likes_cache_key = f"likes_set_{user_id}"

    user_favs = st.session_state.setdefault(fav_cache_key, set())
    user_likes = st.session_state.setdefault(likes_cache_key, set())

    is_fav = catalog_id in user_favs
    is_liked = catalog_id in user_likes

    c_play, c_info, c_like, c_fav = st.columns([1.1, 1, 1, 1])

    with c_play:
        st.link_button("▶", effective_trailer_url, key=f"{key_prefix}_play_{catalog_id}", help=f"Play trailer for {clean_title}", use_container_width=True)

    with c_info:
        if st.button("ℹ️", key=f"{key_prefix}_info_{catalog_id}", help="View Details & Related Movies", use_container_width=True):
            st.session_state["selected_movie_id"] = catalog_id
            st.session_state["selected_movie_data"] = movie
            if in_dialog:
                st.session_state["return_to_ai_dialog_after_details"] = True
                st.session_state["show_ai_dialog"] = False
                st.session_state["show_movie_details"] = True
                st.rerun()
            else:
                show_movie_details_dialog(movie, user_id)

    with c_like:
        like_icon = "❤️" if is_liked else "🤍"
        if st.button(like_icon, key=f"{key_prefix}_like_{catalog_id}", help="Like / Unlike", use_container_width=True):
            liked_now = api_client.toggle_like(user_id, catalog_id)
            if liked_now:
                user_likes.add(catalog_id)
                st.toast(f"Liked '{clean_title}'", icon="❤️")
            else:
                user_likes.discard(catalog_id)
                st.toast(f"Unliked '{clean_title}'", icon="🤍")
            st.rerun()

    with c_fav:
        fav_icon = "🔖" if is_fav else "➕"
        if st.button(fav_icon, key=f"{key_prefix}_fav_{catalog_id}", help="Watchlist", use_container_width=True):
            if is_fav:
                api_client.remove_favorite(user_id, catalog_id)
                user_favs.discard(catalog_id)
                st.toast(f"Removed '{clean_title}' from Watchlist", icon="🗑️")
            else:
                api_client.add_favorite(
                    user_id=user_id,
                    movie_id=catalog_id,
                    movie_title=clean_title,
                    genres=genres_str,
                    release_date=str(year),
                    rating=rating_val
                )
                user_favs.add(catalog_id)
                st.toast(f"Saved '{clean_title}' to Watchlist!", icon="🔖")
            st.rerun()


# -----------------------------------------------------------------------------
# 5. Top 10 Ranked Movie Carousel (With Large Translucent Numbers)
# -----------------------------------------------------------------------------
def _on_carousel_nav(page_key: str, delta: int, total_pages: int):
    """Atomic carousel page navigation callback executed before rerun."""
    current = st.session_state.get(page_key, 0)
    st.session_state[page_key] = (current + delta) % max(1, total_pages)


def render_ranked_carousel(
    title: str,
    subtitle: str,
    movies: List[Dict[str, Any]],
    user_id: str,
    section_id: str,
    limit_per_page: int = 5,
    show_score: bool = False
):
    """
    Renders a streaming ranked carousel featuring giant translucent numbers (1, 2, 3...)
    sitting behind/beside each movie card, directly matching the reference visual design.
    """
    if not movies:
        return

    page_key = f"ranked_carousel_page_{section_id}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    total_movies = min(len(movies), 20)  # Top 20 ranked
    total_pages = max(1, (total_movies + limit_per_page - 1) // limit_per_page)

    st.session_state[page_key] = st.session_state[page_key] % total_pages
    current_page = st.session_state[page_key]

    # Section Header
    head_col1, head_col2 = st.columns([4.2, 1.4])
    with head_col1:
        st.markdown(
            f"""
            <div class="section-heading-row">
                <div class="section-title-wrap">
                    <span class="section-red-icon" style="color: #00E5FF;">👑</span>
                    <span class="section-title-text">{html.escape(title)}</span>
                </div>
            </div>
            <div class="section-subtitle-text">{html.escape(subtitle)}</div>
            """,
            unsafe_allow_html=True
        )

    with head_col2:
        if total_pages > 1:
            p_col, c_col, n_col = st.columns([1, 1.4, 1])
            with p_col:
                st.button("◀", key=f"prev_{section_id}", on_click=_on_carousel_nav, args=(page_key, -1, total_pages), use_container_width=True)
            with c_col:
                st.markdown(
                    f'<div style="text-align: center; font-size: 0.85rem; font-weight: 700; color: #94A3B8; padding-top: 6px;">'
                    f'{current_page + 1} / {total_pages}</div>',
                    unsafe_allow_html=True
                )
            with n_col:
                st.button("▶", key=f"next_{section_id}", on_click=_on_carousel_nav, args=(page_key, 1, total_pages), use_container_width=True)

    start_idx = current_page * limit_per_page
    paged_movies = movies[start_idx : start_idx + limit_per_page]

    cols = st.columns(min(len(paged_movies), limit_per_page))
    for idx, movie in enumerate(paged_movies):
        rank = start_idx + idx + 1
        with cols[idx]:
            # Giant Translucent Ranking Number
            st.markdown(
                f"""
                <div style="position: relative; margin-bottom: -35px; z-index: 1;">
                    <div class="ranked-card-number">{rank}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            render_movie_card(
                movie=movie,
                user_id=user_id,
                key_prefix=f"{section_id}_r{rank}",
                show_score=show_score
            )


# -----------------------------------------------------------------------------
# 6. Standard Horizontal Movie Carousel
# -----------------------------------------------------------------------------
def render_movie_carousel(
    title: str,
    subtitle: str,
    movies: List[Dict[str, Any]],
    user_id: str,
    section_id: str,
    limit_per_page: int = 6,
    show_score: bool = False
):
    """
    Renders a standard streaming horizontal carousel with atomic pagination controls.
    """
    if not movies:
        return

    page_key = f"carousel_page_{section_id}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    total_movies = len(movies)
    total_pages = max(1, (total_movies + limit_per_page - 1) // limit_per_page)

    st.session_state[page_key] = st.session_state[page_key] % total_pages
    current_page = st.session_state[page_key]

    head_col1, head_col2 = st.columns([4.2, 1.4])
    with head_col1:
        st.markdown(
            f"""
            <div class="section-heading-row">
                <div class="section-title-wrap">
                    <span class="section-red-icon" style="color: #00E5FF;">▶</span>
                    <span class="section-title-text">{html.escape(title)}</span>
                </div>
            </div>
            <div class="section-subtitle-text">{html.escape(subtitle)}</div>
            """,
            unsafe_allow_html=True
        )

    with head_col2:
        if total_pages > 1:
            p_col, c_col, n_col = st.columns([1, 1.4, 1])
            with p_col:
                st.button("◀", key=f"prev_{section_id}", on_click=_on_carousel_nav, args=(page_key, -1, total_pages), use_container_width=True)
            with c_col:
                st.markdown(
                    f'<div style="text-align: center; font-size: 0.85rem; font-weight: 700; color: #94A3B8; padding-top: 6px;">'
                    f'{current_page + 1} / {total_pages}</div>',
                    unsafe_allow_html=True
                )
            with n_col:
                st.button("▶", key=f"next_{section_id}", on_click=_on_carousel_nav, args=(page_key, 1, total_pages), use_container_width=True)

    start_idx = current_page * limit_per_page
    paged_movies = movies[start_idx : start_idx + limit_per_page]

    cols = st.columns(min(len(paged_movies), limit_per_page))
    for idx, movie in enumerate(paged_movies):
        with cols[idx]:
            render_movie_card(
                movie=movie,
                user_id=user_id,
                key_prefix=f"{section_id}_p{current_page}_{idx}",
                show_score=show_score
            )


# -----------------------------------------------------------------------------
# 7. Helper Components: Header, Metric Card, Empty State, Genre Tiles, Footer
# -----------------------------------------------------------------------------
def render_header(subtitle: str = "Discover your next favorite."):
    """Renders top branding header with Cinevora Cinzel wordmark."""
    st.markdown(
        f"""
        <div style="margin-bottom: 18px;">
            <div class="cinevora-brand">Cinevora</div>
            <div class="cinevora-tagline">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metric_card(label: str, value: Any, subtext: str = "", border_color: Optional[str] = None):
    """Renders a styled dark metric card."""
    b_color = border_color or "#00E5FF"
    st.markdown(
        f"""
        <div class="metric-card-box" style="border-left: 4px solid {b_color};">
            <div class="metric-card-label">{html.escape(label)}</div>
            <div class="metric-card-value">{html.escape(str(value))}</div>
            <div class="metric-card-sub">{html.escape(subtext)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_empty_state(title: str, message: str, icon: str = "🎬"):
    """Displays an elegant cinema empty-state widget."""
    st.markdown(
        f"""
        <div style="
            background: #0E1622;
            border: 1px dashed rgba(255, 255, 255, 0.15);
            border-radius: 14px;
            padding: 38px 24px;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        ">
            <div style="font-size: 2.8rem; margin-bottom: 10px;">{icon}</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF; margin-bottom: 6px; font-family: 'Cinzel', serif;">
                {html.escape(title)}
            </div>
            <div style="font-size: 0.92rem; color: #94A3B8; max-width: 520px; margin: 0 auto; line-height: 1.5;">
                {html.escape(message)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_genre_tiles(on_click_genre_callback=None):
    """Renders clickable category tiles."""
    genre_icons = {
        "Action": "💥",
        "Adventure": "🗺️",
        "Animation": "🎨",
        "Comedy": "😂",
        "Crime": "🕵️",
        "Drama": "🎭",
        "Horror": "👻",
        "Romance": "❤️",
        "Sci-Fi": "🚀",
        "Thriller": "⚡"
    }

    cols = st.columns(5)
    for idx, (genre, icon) in enumerate(genre_icons.items()):
        col = cols[idx % 5]
        with col:
            tile_key = f"genre_tile_btn_{genre}"
            if st.button(f"{icon}\n{genre}", key=tile_key, use_container_width=True):
                st.session_state["nav_selection"] = "Explore"
                st.session_state["explore_genre_filter"] = genre
                if on_click_genre_callback:
                    on_click_genre_callback(genre)
                st.rerun()


def render_footer():
    """Renders the Cinevora cinematic streaming footer."""
    st.markdown(
        """
        <div class="cinevora-footer">
            <div class="cinevora-footer-left">
                <div class="cinevora-footer-brand">CINEVORA</div>
                <div>Premium Cinema Discovery Platform — Indian Cinema & Hollywood Catalog (3,560 verified titles).</div>
                <div style="font-size: 0.78rem; color: #64748B; margin-top: 4px;">Powered by FastAPI, Streamlit, and Google Gemini 3.5 Flash Lite.</div>
            </div>
            <div style="font-size: 0.8rem; color: #64748B; text-align: right;">
                © 2026 Cinevora • Single Source of Truth: <code>Movies_Master_Cleaned.csv</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
