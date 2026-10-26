"""
Cinevora Home Page View (Streaming Discovery & Cinematic Redesign)
Follows the reference streaming layout:
1. Top Navbar (Handled in app.py with brand lockup, 8 destinations, compact search, user switcher)
2. Compact search input / quick exploration directly beneath the navbar
3. Large Dynamic Rotating Hero Banner (16:9 landscape backdrop, dark gradient overlay, 
   prominent typography, trailers, and client-side 7s timer)
4. Horizontal carousel: 'Popular on Cinevora'
5. Horizontal carousel: 'Recommended for You' (Dynamic taste profile based on searches & likes)
6. Horizontal carousel: 'Trending Action & Sci-Fi'
7. Section: 'Explore by Genre' (Clickable category tiles)
8. Horizontal carousel: 'Highest Rated Classics'
9. Cinevora Cinematic Footer
"""

import html
import re
import streamlit as st

from frontend.api_client import api_client
from frontend.components import (
    render_rotating_hero_banner,
    render_streaming_hero_banner,
    render_movie_carousel,
    render_ranked_carousel,
    render_genre_tiles,
    render_footer,
    render_movie_card,
    show_movie_details_dialog
)
from src.recommender import master_content_recommender
try:
    from frontend.poster_service import (
        get_movie_enrichment,
        get_indian_movies,
        get_hollywood_movies,
        get_movies_by_language,
        extract_release_year
    )
except ImportError:
    from poster_service import (  # type: ignore
        get_movie_enrichment,
        get_indian_movies,
        get_hollywood_movies,
        get_movies_by_language,
        extract_release_year
    )



def render_home_page(user_id: str, set_nav_callback=None):
    """Renders the Cinevora Home view in Premium Streaming Light mode."""

    # -------------------------------------------------------------------------
    # Handle Hero Banner Action Query Parameters (Watchlist, Like, Details)
    # -------------------------------------------------------------------------
    if "hero_action" in st.query_params:
        action = st.query_params.get("hero_action")
        m_id_val = st.query_params.get("m_id")
        if m_id_val:
            m_id = str(m_id_val).strip()
            if action == "like":
                liked_now = api_client.toggle_like(user_id, m_id)
                likes_set = st.session_state.setdefault(f"likes_set_{user_id}", set())
                if liked_now:
                    likes_set.add(m_id)
                    st.toast("Liked movie!", icon="❤️")
                else:
                    likes_set.discard(m_id)
                    st.toast("Unliked movie", icon="🤍")
            elif action == "fav":
                fav_set = st.session_state.setdefault(f"fav_set_{user_id}", set())
                if m_id in fav_set:
                    api_client.remove_favorite(user_id, m_id)
                    fav_set.discard(m_id)
                    st.toast("Removed movie from Watchlist", icon="🗑️")
                else:
                    meta = get_movie_enrichment(m_id)
                    title = meta.get("title", f"Movie {m_id}")
                    api_client.add_favorite(
                        user_id=user_id,
                        movie_id=m_id,
                        movie_title=title,
                        genres=meta.get("genres", meta.get("genre", "")),
                        rating=meta.get("avg_rating", meta.get("rating"))
                    )
                    fav_set.add(m_id)
                    st.toast(f"Saved '{title}' to Watchlist!", icon="🔖")
            elif action == "details":
                meta = get_movie_enrichment(m_id)
                if meta:
                    st.session_state["selected_movie_id"] = m_id
                    st.session_state["selected_movie_data"] = meta
                    st.session_state["show_movie_details"] = True

        st.query_params.clear()
        st.rerun()

    # -------------------------------------------------------------------------
    # SECTION 2: Edge-to-Edge Cinematic Hero Spotlight (Primary Visual Focus)
    # -------------------------------------------------------------------------
    render_streaming_hero_banner(user_id=user_id)

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 4: Top 10 Blockbusters in India Today (Translucent Ranking Numbers)
    # -------------------------------------------------------------------------
    indian_all = get_indian_movies()
    top_10_indian = sorted(
        indian_all,
        key=lambda m: float(m.get("avg_rating") or m.get("rating") or 0.0),
        reverse=True
    )[:10]

    render_ranked_carousel(
        title="Top 10 Blockbusters in India Today",
        subtitle="The highest-rated cinematic hits and audience sensations across Indian Cinema",
        movies=top_10_indian,
        user_id=user_id,
        section_id="home_top_10_ranked",
        limit_per_page=5
    )

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 5: Multi-Signal Personalized Recommendations ("Recommended for You")
    # -------------------------------------------------------------------------
    personalized_recs = master_content_recommender.recommend_for_user(
        user_id=user_id,
        limit=12,
        exclude_rated=True
    )
    if personalized_recs:
        render_movie_carousel(
            title="Recommended for You",
            subtitle="Curated by Cinevora's master content engine using your likes, watchlist, and viewing habits",
            movies=personalized_recs,
            user_id=user_id,
            section_id="home_personalized_recs",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # Section 5B: "Because You Liked [Movie Title]"
    liked_signal = master_content_recommender.recommend_because_you_liked(user_id=user_id, limit=6)
    if liked_signal.get("source_movie") and liked_signal.get("movies"):
        src_movie_title = re.sub(r"\s*\(\d{4}\)", "", liked_signal["source_movie"].get("title", "")).strip()
        render_movie_carousel(
            title=f"Because You Liked '{src_movie_title}'",
            subtitle="Titles sharing director, cast, or genre affinities with your recently liked movie",
            movies=liked_signal["movies"],
            user_id=user_id,
            section_id="home_because_liked",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # Section 5C: "More Like Movies in Your Watchlist"
    wl_signal = master_content_recommender.recommend_from_watchlist(user_id=user_id, limit=6)
    if wl_signal.get("source_movie") and wl_signal.get("movies"):
        wl_movie_title = re.sub(r"\s*\(\d{4}\)", "", wl_signal["source_movie"].get("title", "")).strip()
        render_movie_carousel(
            title=f"More Like '{wl_movie_title}' in Your Watchlist",
            subtitle="Recommendations connected to saved titles on your radar",
            movies=wl_signal["movies"],
            user_id=user_id,
            section_id="home_from_watchlist",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # Section 5D: "Discover Something New" (Exploration)
    discover_recs = master_content_recommender.recommend_discover_new(user_id=user_id, limit=6)
    if discover_recs:
        render_movie_carousel(
            title="Discover Something New",
            subtitle="Critically acclaimed masterworks from industries and genres you haven't explored yet",
            movies=discover_recs,
            user_id=user_id,
            section_id="home_discover_new",
            limit_per_page=6
        )
        st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 6: Trending Indian Cinema
    # -------------------------------------------------------------------------
    render_movie_carousel(
        title="Trending Indian Cinema",
        subtitle="Blockbuster epics, action sensations, and acclaimed dramas across India",
        movies=indian_all,
        user_id=user_id,
        section_id="home_trending_indian",
        limit_per_page=6
    )

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 7: Popular Hollywood Movies
    # -------------------------------------------------------------------------
    hollywood_all = get_hollywood_movies()
    merged_hollywood = sorted(
        hollywood_all,
        key=lambda m: float(m.get("avg_rating") or m.get("rating") or 0.0),
        reverse=True
    )

    render_movie_carousel(
        title="Popular Hollywood Blockbusters",
        subtitle="Visionary sci-fi, ground-breaking thrillers, and iconic modern blockbusters",
        movies=merged_hollywood,
        user_id=user_id,
        section_id="home_popular_hollywood",
        limit_per_page=6
    )

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 7: Tamil Cinema (தமிழ்)
    # -------------------------------------------------------------------------
    tamil_movies = get_movies_by_language("ta")
    render_movie_carousel(
        title="Tamil Cinema (தமிழ்)",
        subtitle="Riveting thrillers, intense character dramas, and electrifying spectacles",
        movies=tamil_movies,
        user_id=user_id,
        section_id="home_tamil_cinema",
        limit_per_page=6
    )

    # -------------------------------------------------------------------------
    # SECTION 8: Telugu Cinema (తెలుగు)
    # -------------------------------------------------------------------------
    telugu_movies = get_movies_by_language("te")
    render_movie_carousel(
        title="Telugu Cinema (తెలుగు)",
        subtitle="Larger-than-life storytelling, heroic epics, and timeless romances",
        movies=telugu_movies,
        user_id=user_id,
        section_id="home_telugu_cinema",
        limit_per_page=6
    )

    # -------------------------------------------------------------------------
    # SECTION 9: Hindi Cinema (हिन्दी)
    # -------------------------------------------------------------------------
    hindi_movies = get_movies_by_language("hi")
    render_movie_carousel(
        title="Hindi Cinema (हिन्दी)",
        subtitle="Inspirational biographical dramas and evergreen comedic masterworks",
        movies=hindi_movies,
        user_id=user_id,
        section_id="home_hindi_cinema",
        limit_per_page=6
    )

    # -------------------------------------------------------------------------
    # SECTION 10: Malayalam & Kannada Cinema (മലയാളം & ಕನ್ನಡ)
    # -------------------------------------------------------------------------
    south_gems = get_movies_by_language("ml") + get_movies_by_language("kn")
    render_movie_carousel(
        title="Malayalam & Kannada Cinema",
        subtitle="Folkloric legends, intense survival sagas, and heartfelt slice-of-life journeys",
        movies=south_gems,
        user_id=user_id,
        section_id="home_malayalam_kannada",
        limit_per_page=6
    )

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 11: Explore by Genre (Clickable Category Tiles)
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div style="margin-top: 26px; margin-bottom: 12px; border-bottom: 1px solid #E5E7EB; padding-bottom: 6px;">
            <div style="font-family: 'Cinzel', serif; font-size: 1.35rem; font-weight: 800; color: #111827; letter-spacing: 0.02em;">
                🎬 Explore by Genre
            </div>
            <div style="font-size: 0.84rem; color: #4B5563;">
                Browse curated collections tailored to every cinematic taste
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    render_genre_tiles()

    st.markdown('<div class="cinevora-section-divider"></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SECTION 12: Highest Rated All-Time
    # -------------------------------------------------------------------------
    top_res = api_client.search_movies(sort_by="rating", limit=18)
    top_movies = top_res.get("results", [])

    render_movie_carousel(
        title="Highest Rated Masterpieces",
        subtitle="Critically acclaimed masterpieces with top viewer ratings across catalog history",
        movies=top_movies,
        user_id=user_id,
        section_id="home_top_rated",
        limit_per_page=6
    )

    # -------------------------------------------------------------------------
    # SECTION 13: Cinevora Footer
    # -------------------------------------------------------------------------
    render_footer()
